"""
Statistics callbacks module.

Handles incremental cache updates when events occur, computes book-level
metrics on-demand, and provides cache rebuild functionality.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from ..model import (BookEntry, BookStatisticsModel, LendingStatusEntry,
                     MonthBookEntry, PagesInLentPeriodEntry,
                     PagesReadPeriodEntry, PeriodHistoryEntry,
                     StatisticalEvent, Statistics)
from ..storage import (JsonFileStorage, JsonIdNumeralStorage, LibroStorage,
                       OnObjectAddCtx)

logger = logging.getLogger(__name__)


# helpers

def _date_str(timestamp: float) -> str:
    """Convert a timestamp to a date string (YYYY-MM-DD)."""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")


def _month_str(timestamp: float) -> str:
    """Convert a timestamp to a month string (YYYY-MM)."""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m")


# callbacks related to statistics, these are defined here, so they can be registered in other classes

def on_reading_event_added(ctx: OnObjectAddCtx[StatisticalEvent]):
    """Handle a new statistical event and update the cached statistics.

    The logic mirrors the original implementation but ensures that the
    ``books_lent`` count is incremented for *every* lend event, not just for
    unique book IDs.
    """
    event = ctx.obj
    stats_storage: JsonFileStorage[Statistics] = LibroStorage.get(
        JsonFileStorage[Statistics], Statistics
    )
    stats = stats_storage.get() or Statistics()

    date_key = _date_str(event.timestamp)
    month_key = _month_str(event.timestamp)

    if event.book_read is not None:
        delta = event.book_read.pages_read - event.book_read.previous_pages_read
        if delta != 0:
            entry = stats.pages_read_by_period.get(
                date_key, PagesReadPeriodEntry()
            )
            entry.pages += delta
            if entry.pages <= 0:
                del stats.pages_read_by_period[date_key]
            else:
                stats.pages_read_by_period[date_key] = entry

    elif event.book_finished is not None:
        month_entry = stats.books_finished_by_period.get(
            month_key, MonthBookEntry()
        )
        if event.book_id not in month_entry.book_ids:
            month_entry.count += 1
            month_entry.book_ids.append(event.book_id)
        stats.books_finished_by_period[month_key] = month_entry

    elif event.book_lent is not None:
        month_entry = stats.books_lent_by_period.get(
            month_key, MonthBookEntry()
        )
        month_entry.count += 1  # count every lend event
        if event.book_id not in month_entry.book_ids:
            month_entry.book_ids.append(event.book_id)
        stats.books_lent_by_period[month_key] = month_entry

        pages_entry = stats.pages_in_lent_by_period.get(
            month_key, PagesInLentPeriodEntry()
        )
        pages_entry.total_pages += event.book_lent.total_pages
        month_count = month_entry.count
        pages_entry.avg_pages_per_book = (
            pages_entry.total_pages / month_count if month_count > 0 else 0.0
        )
        stats.pages_in_lent_by_period[month_key] = pages_entry

    elif event.book_returned is not None:
        lend_id = event.book_returned.lend_id
        overdue = event.book_returned.overdue_time is not None
        stats.lending_status[lend_id] = LendingStatusEntry(
            status="returned_overdue" if overdue else "returned_on_time",
            return_date=event.timestamp,
            overdue_days=int(event.book_returned.overdue_time // 86400) if event.book_returned.overdue_time else 0,
        )

    stats.last_updated_timestamp = event.timestamp
    stats_storage.update(stats)
    stats_storage.save()


def register_statistics_callbacks():
    """
    Register the event listener on the reading_events storage.
    Called once during app initialization.
    """
    events_storage: JsonIdNumeralStorage[StatisticalEvent] = LibroStorage.get(
        JsonIdNumeralStorage[StatisticalEvent], StatisticalEvent
    )
    events_storage.register_add_callback(on_reading_event_added)


def _week_str(timestamp: float) -> str:
    """Convert a timestamp to an ISO week string (YYYY-Www)."""
    dt = datetime.fromtimestamp(timestamp)
    iso = dt.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _compute_weekly_monthly_aggregates(
    read_events: list[StatisticalEvent],
    total_pages: int,
    current_page: int,
) -> tuple[Optional[int], Optional[int], Optional[int],
           Optional[float], Optional[float],
           list['PeriodHistoryEntry'], list['PeriodHistoryEntry']]:
    """
    Group read events by week and month to compute aggregate stats.

    Returns:
        (this_week_pages, this_month_pages, last_month_pages,
         this_week_progress, this_month_progress,
         weekly_history, monthly_history)
    """

    # --- group deltas by ISO week and calendar month ---
    week_pages: dict[str, int] = {}
    month_pages: dict[str, int] = {}

    for event in read_events:
        book_read = event.book_read
        assert book_read is not None
        delta = book_read.pages_read - book_read.previous_pages_read
        if delta <= 0:
            continue  # skip backward/zero moves for period aggregates

        wk = _week_str(event.timestamp)
        week_pages[wk] = week_pages.get(wk, 0) + delta

        mo = _month_str(event.timestamp)
        month_pages[mo] = month_pages.get(mo, 0) + delta

    now = datetime.now()

    # current week / month
    cur_week = _week_str(now.timestamp())
    cur_month = _month_str(now.timestamp())

    # last month
    last_month_dt = datetime(now.year, now.month, 1) - timedelta(days=1)
    last_month = _month_str(last_month_dt.timestamp())

    this_week_pages = week_pages.get(cur_week)
    this_month_pages = month_pages.get(cur_month)
    last_month_pages = month_pages.get(last_month)

    # progress percent this week / this month
    this_week_progress: Optional[float] = None
    if this_week_pages is not None and total_pages > 0:
        this_week_progress = this_week_pages / total_pages

    this_month_progress: Optional[float] = None
    if this_month_pages is not None and total_pages > 0:
        this_month_progress = this_month_pages / total_pages

    # --- build weekly history (last 10 weeks) ---
    sorted_weeks = sorted(week_pages.keys())
    recent_weeks = sorted_weeks[-10:] if len(sorted_weeks) > 10 else sorted_weeks
    # provide readable labels like "Jun 1" (the Monday of that week)
    weekly_history: list[PeriodHistoryEntry] = []
    for wk in recent_weeks:
        try:
            yr = int(wk.split("-W")[0])
            wn = int(wk.split("-W")[1])
            # approximate: use the Monday of the ISO week
            from datetime import date as dt_date
            monday = dt_date.fromisocalendar(yr, wn, 1)
            label = monday.strftime("%b %d")
        except Exception:
            label = wk
        weekly_history.append(PeriodHistoryEntry(label=label, pages=week_pages[wk]))

    # --- build monthly history (last 12 months) ---
    sorted_months = sorted(month_pages.keys())
    recent_months = sorted_months[-12:] if len(sorted_months) > 12 else sorted_months
    monthly_history: list[PeriodHistoryEntry] = []
    for mo in recent_months:
        try:
            dt_mo = datetime.strptime(mo, "%Y-%m")
            label = dt_mo.strftime("%b %Y")
        except Exception:
            label = mo
        monthly_history.append(PeriodHistoryEntry(label=label, pages=month_pages[mo]))

    return (
        this_week_pages, this_month_pages, last_month_pages,
        this_week_progress, this_month_progress,
        weekly_history, monthly_history,
    )


def compute_book_statistics(book: BookEntry, book_id: int) -> BookStatisticsModel:
    """
    Compute reading statistics for a single book from all recorded events.

    Algorithm:
      1. Fetch all StatisticalEvents from storage.
      2. Filter events where event.book_id == book.id and event.book_read is not None.
      3. Sort by timestamp.
      4. Compute per-session deltas from the event fields.
      5. Calculate aggregate metrics including weekly/monthly aggregates.
    """
    events_storage: JsonIdNumeralStorage[StatisticalEvent] = LibroStorage.get(
        JsonIdNumeralStorage[StatisticalEvent], StatisticalEvent
    )

    # get all events for this book with book_read field
    read_events: list[StatisticalEvent] = []
    finished_event: Optional[StatisticalEvent] = None

    for event in events_storage.objects.values():
        if event.book_id != book_id:
            continue
        if event.book_read is not None:
            read_events.append(event)
        if event.book_finished is not None:
            finished_event = event

    if not read_events:
        return BookStatisticsModel(book_id=book_id)

    read_events.sort(key=lambda e: e.timestamp)

    # calculate total pages read (sum of all deltas, including negative/backward)
    total_pages_read = 0
    for event in read_events:
        book_read = event.book_read
        assert book_read is not None
        delta = book_read.pages_read - book_read.previous_pages_read
        total_pages_read += delta
        if delta <= 0:
            logger.warning(
                "Backward progress detected for book %d: %d -> %d (delta=%d)",
                book_id,
                book_read.previous_pages_read,
                book_read.pages_read,
                delta,
            )

    if total_pages_read <= 0:
        return BookStatisticsModel(book_id=book_id)

    # count unique days with progress
    unique_dates = {_date_str(e.timestamp) for e in read_events}
    days_reading = len(unique_dates)

    if days_reading <= 0:
        return BookStatisticsModel(book_id=book_id)

    pages_read_per_day = total_pages_read / days_reading

    # total pages for progress calculations
    total_pages = book.pages if book.pages else 1
    current_page = book.current_page or 0

    # weekly / monthly aggregates
    total_pages_for_pct = book.pages if book.pages else 1
    (this_week_pages, this_month_pages, last_month_pages,
     this_week_progress, this_month_progress,
     weekly_history, monthly_history) = _compute_weekly_monthly_aggregates(
        read_events, total_pages_for_pct, current_page,
    )

    # total reading time (if book is finished)
    total_reading_time_hours: Optional[float] = None
    if finished_event is not None:
        first_event_time = read_events[0].timestamp
        last_event_time = finished_event.timestamp
        duration_seconds = last_event_time - first_event_time
        total_reading_time_hours = duration_seconds / 3600

        # also recalculate days_to_finish if finishing event exists
        if finished_event.book_finished is not None:
            days_to_finish = duration_seconds / 86400
            finished_event.book_finished.days_to_finish = days_to_finish
            finished_event.book_finished.active_days_to_finish = days_reading

    return BookStatisticsModel(
        book_id=book_id,
        pages_read_per_day=pages_read_per_day,
        days_reading=days_reading,
        this_week_pages=this_week_pages,
        this_month_pages=this_month_pages,
        last_month_pages=last_month_pages,
        this_week_progress=this_week_progress,
        this_month_progress=this_month_progress,
        weekly_history=weekly_history,
        monthly_history=monthly_history,
    )

# caching

def rebuild_statistics_cache() -> Statistics:
    """
    Rebuild the Statistics cache from scratch by scanning all events.
    Used when cache is missing or stale.
    """
    events_storage: JsonIdNumeralStorage[StatisticalEvent] = LibroStorage.get(
        JsonIdNumeralStorage[StatisticalEvent], StatisticalEvent
    )

    stats = Statistics()

    for event in events_storage.objects.values():
        date_key = _date_str(event.timestamp)
        month_key = _month_str(event.timestamp)

        if event.book_read is not None:
            delta = event.book_read.pages_read - event.book_read.previous_pages_read
            if delta != 0:
                entry = stats.pages_read_by_period.get(
                    date_key, PagesReadPeriodEntry()
                )
                entry.pages += delta
                if entry.pages <= 0:
                    del stats.pages_read_by_period[date_key]
                else:
                    stats.pages_read_by_period[date_key] = entry

        elif event.book_finished is not None:
            month_entry = stats.books_finished_by_period.get(
                month_key, MonthBookEntry()
            )
            if event.book_id not in month_entry.book_ids:
                month_entry.count += 1
                month_entry.book_ids.append(event.book_id)
        elif event.book_lent is not None:
            # Increment the total number of lend events for the month.
            month_entry = stats.books_lent_by_period.get(
                month_key, MonthBookEntry()
            )
            month_entry.count += 1
            if event.book_id not in month_entry.book_ids:
                month_entry.book_ids.append(event.book_id)
            stats.books_lent_by_period[month_key] = month_entry

            # track pages in lent
            pages_entry = stats.pages_in_lent_by_period.get(
                month_key, PagesInLentPeriodEntry()
            )
            pages_entry.total_pages += event.book_lent.total_pages
            month_count = month_entry.count
            pages_entry.avg_pages_per_book = (
                pages_entry.total_pages / month_count if month_count > 0 else 0.0
            )
            stats.pages_in_lent_by_period[month_key] = pages_entry
            stats.pages_in_lent_by_period[month_key] = pages_entry

        elif event.book_returned is not None:
            lend_id = event.book_returned.lend_id
            overdue = event.book_returned.overdue_time is not None
            stats.lending_status[lend_id] = LendingStatusEntry(
                status="returned_overdue" if overdue else "returned_on_time",
                return_date=event.timestamp,
                overdue_days=(
                    int(event.book_returned.overdue_time // 86400)
                    if event.book_returned.overdue_time
                    else 0
                ),
            )

    stats.last_updated_timestamp = (
        max(events_storage.objects.keys()) if events_storage.objects else 0.0
    )

    return stats


def ensure_statistics_cache():
    """
    Load or rebuild the statistics cache on app launch.
    If cache is missing or stale, rebuild from events.
    """
    stats_storage: JsonFileStorage[Statistics] = LibroStorage.get(
        JsonFileStorage[Statistics], Statistics
    )

    stats = stats_storage.get()
    if stats is None:
        stats = Statistics()

    if (
        stats.last_updated_timestamp == 0.0
        or not stats.books_finished_by_period
    ):
        logger.info("Statistics cache missing or empty, rebuilding from events...")
        rebuilt = rebuild_statistics_cache()
        stats_storage.update(rebuilt)
        stats_storage.save()
        return

    logger.info("Statistics cache loaded (last updated: %s)", stats.last_updated_timestamp)