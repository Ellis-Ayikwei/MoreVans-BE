from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_booking_confirmation_email(request_data):
    """
    Send a booking confirmation email to the customer
    """
    try:
        # Prepare email data
        subject = f'Booking Confirmation - {request_data.tracking_number}'
        
        # Prepare context for email template
        context = {
            'tracking_number': request_data.tracking_number,
            'customer_name': request_data.contact_name,
            'price': request_data.price,
            'pickup_location': request_data.journey_stops.filter(type='pickup').first().location if request_data.journey_stops.filter(type='pickup').exists() else None,
            'dropoff_location': request_data.journey_stops.filter(type='dropoff').first().location if request_data.journey_stops.filter(type='dropoff').exists() else None,
            'staff_count': request_data.staff_required,
            'contact_email': request_data.contact_email,
            'contact_phone': request_data.contact_phone,
        }

        # Render email template
        html_message = render_to_string('emails/booking_confirmation.html', context)
        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request_data.contact_email],
            html_message=html_message,
            fail_silently=False,
        )

        return True
    except Exception as e:
        print(f"Error sending confirmation email: {str(e)}")
        return False 