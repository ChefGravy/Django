from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render
from django.contrib import messages
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
import json
import urllib.request
import urllib.error
import re
from frontpage import models
from frontpage.models import ContactForm
from .forms import ContactForm

AI_SYSTEM_PROMPT = """You are the PRP Real Estate AI Assistant, an objective and knowledgeable intelligence engine for Seattle and King County, Washington.

Your capabilities and knowledge include:
- Seattle neighborhoods (Ballard, Fremont, Queen Anne, Capitol Hill, West Seattle, Greenwood, Phinney Ridge, South Lake Union, Wallingford, etc.)
- Local amenities, parks (Gas Works, Kerry Park, Alki Beach, Discovery Park, Volunteer Park), dining, and cultural attractions
- Transit connectivity (Sound Transit 1 Line Light Rail, RapidRide lines, bus networks, West Seattle Water Taxi, bike corridors like the Burke-Gilman Trail)
- King County real estate fundamentals, property tax assessment processes, typical architectural styles (Craftsman, Mid-century, Pacific Northwest Modern, Victorian, Condos)
- Balanced, objective comparisons of neighborhood character, walkability, and commute times.

Style and Safety Rules:
- Always respond in fluent, professional, objective English.
- Do NOT provide first-person personal opinions or bias.
- Keep responses concise and readable (typically 2-4 focused paragraphs or structured bullet points, under 150 words).
- If asked for legal advice, structural engineering, or specific investment guarantees, provide a polite disclaimer advising consultation with licensed professionals."""

@csrf_exempt
@require_POST
def ai_assistant_api(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    user_message = data.get('message', '').strip()
    if not user_message:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)

    if len(user_message) > 600:
        return JsonResponse({'error': 'Message too long (max 600 characters)'}, status=400)

    wants_stream = data.get('stream', True)

    payload = {
        'model': 'qwen2.5:7b',
        'messages': [
            {'role': 'system', 'content': AI_SYSTEM_PROMPT},
            {'role': 'user', 'content': user_message}
        ],
        'options': {
            'num_predict': 220,
            'temperature': 0.7,
            'top_p': 0.9,
        },
        'stream': True
    }

    if not wants_stream:
        payload['stream'] = False
        try:
            req = urllib.request.Request(
                'http://127.0.0.1:11434/api/chat',
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                res_data = json.loads(resp.read().decode('utf-8'))
                reply = res_data.get('message', {}).get('content', '')
                return JsonResponse({'reply': reply, 'model': 'qwen2.5:7b'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def stream_tokens():
        try:
            req = urllib.request.Request(
                'http://127.0.0.1:11434/api/chat',
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                for line in resp:
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        token = chunk.get('message', {}).get('content', '')
                        if token:
                            yield token
                        if chunk.get('done'):
                            break
                    except Exception:
                        continue
        except urllib.error.URLError as e:
            yield f"\n[AI Assistant Notice: Local neural model is currently busy. Please retry shortly. ({getattr(e, 'reason', str(e))})]"
        except Exception as e:
            yield f"\n[Inference error: {str(e)}]"

    response = StreamingHttpResponse(stream_tokens(), content_type='text/plain; charset=utf-8')
    response['Cache-Control'] = 'no-cache, no-transform'
    response['X-Accel-Buffering'] = 'no'
    return response


# Create your views here.
def contact(request):
        if request.method == 'POST':
            # Honeypot check — bots fill this hidden field, humans don't
            if request.POST.get('website', ''):
                return render(request, 'frontpage/contactform.html', {'form': ContactForm()})

            form = ContactForm(request.POST)
            if form.is_valid():
                name = form.cleaned_data['name']
                email = form.cleaned_data['email']
                category = form.cleaned_data['category']
                subject = form.cleaned_data['subject']
                body = form.cleaned_data['body']

                # Gibberish check — reject if body has a long consonant run or fewer than 3 words
                words = body.strip().split()
                if len(words) < 3 or re.search(r'[bcdfghjklmnpqrstvwxyz]{8,}', body, re.IGNORECASE):
                    form = ContactForm()
                    return render(request, 'frontpage/contactform.html', {'form': form})

                form.save()
                #send_mail(subject, message, from_email, fail_silently=True)
                subject_email = 'PRP Real Estate'
                message_email = 'Welcome and thank you for your e-mail! I will be in touch soon.'
                from_email = settings.EMAIL_HOST_USER
                #this e-mail is for owner with all the details
                send_mail(subject, 'Name: ' + name + '\nEmail of sender: ' + email + '\nCategory: ' + category + '\nSubject: ' + subject + '\nBody: '+ body, email, [from_email], fail_silently=True)
                #this e-mail is for user
                send_mail(subject_email, message_email, 'ruslan@uw.edu',[email], fail_silently=True)

        form = ContactForm()
        return render(request, 'frontpage/contactform.html', {'form':form})

class AboutView(TemplateView):
    template_name = 'frontpage/about.html'

    class Meta:
        verbose_name_plural = 'About'

class BlogView(TemplateView):
    template_name = 'frontpage/blog.html'

    class Meta:
        verbose_name_plural = 'Blog'

class DataView(TemplateView):
    template_name = 'frontpage/data.html'

    class Meta:
        verbose_name_plural = 'Data'