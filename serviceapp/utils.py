from datetime import datetime, timedelta
from django.utils import timezone
from .models import AvailabilitySchedule, Appointment


# generate available time slot for clients base on a service provider availability schedule
def get_available_time_slots(provider, service, days_ahead=30):
    available_slots = {}
    now = timezone.localtime()  # current aware datetime in active timezone
    today = now.date()
    slot_duration = service.duration  # minutes

    # Provider’s availability
    availability_schedule = AvailabilitySchedule.objects.filter(
        service_provider=provider
    ).order_by('day_of_week', 'start_time')

    # Existing booked slots
    existing_appointments = Appointment.objects.filter(
        service__provider=provider,
        appointment_date__gte=today,
        appointment_date__lte=today + timedelta(days=days_ahead),
        status__in=['scheduled', 'confirmed']
    ).values_list('appointment_date', 'start_time', 'end_time')

    booked_slots = {}
    for apt_date, start_time, end_time in existing_appointments:
        booked_slots.setdefault(apt_date, []).append((start_time, end_time))

    # Generate slots for each day
    for i in range(days_ahead):
        current_date = today + timedelta(days=i)
        day_availability = availability_schedule.filter(day_of_week=current_date.weekday())
        if not day_availability:
            continue

        date_slots = []

        for schedule in day_availability:
            current_time = datetime.combine(current_date, schedule.start_time)
            end_time = datetime.combine(current_date, schedule.end_time)

            while current_time + timedelta(minutes=slot_duration) <= end_time:
                slot_start = current_time.time()
                slot_end = (current_time + timedelta(minutes=slot_duration)).time()

                # Full aware datetime for this slot
                slot_datetime = timezone.make_aware(datetime.combine(current_date, slot_start))
                
                # Skip if slot is in the past
                if slot_datetime <= now:
                    current_time += timedelta(minutes=slot_duration)
                    continue

                # Check if slot overlaps with existing appointment
                is_available = True
                if current_date in booked_slots:
                    for booked_start, booked_end in booked_slots[current_date]:
                        if slot_start < booked_end and slot_end > booked_start:
                            is_available = False
                            break

                if is_available:
                    date_slots.append({
                        'time': slot_start,
                        'display': slot_start.strftime('%I:%M %p'),
                        'available': True
                    })

                current_time += timedelta(minutes=slot_duration)

        if date_slots:
            available_slots[current_date] = date_slots
    return available_slots