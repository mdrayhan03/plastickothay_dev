from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from bson import ObjectId
from datetime import datetime, timedelta
from superadmin.forms import LoginForm, CustomUserCreationForm
from superadmin.models import User, OTP
from plastickothay.models import Post
import json
import random
from email_control import post_mail, account_verification_mail, password_reset_mail


def get_user(user_id: str) -> User | None:
    try:
        return User.objects.get(pk=ObjectId(user_id))
    except User.DoesNotExist:
        return None
    except Exception:
        return None


def wishes() -> str:
    now = datetime.now()
    hr = now.hour
    if 5 <= hr <= 12:
        return "Morning"
    if 13 <= hr <= 18:
        return "Afternoon"
    return "Evening"


def _is_admin_user(user) -> bool:
    return bool(user) and getattr(user, "user_type", 3) in {1, 2}


def _serialize_pending_post(post) -> dict:
    created_at = getattr(post, "created", None)
    return {
        "id": str(post.id),
        "title": getattr(post, "name", None) or "Untitled report",
        "reporter": getattr(post, "name", None) or getattr(post, "email", None) or "Unknown reporter",
        "created": created_at.strftime("%b %d, %Y") if created_at else "Unknown",
        "status": "Pending",
        "status_value": 2,
        "email": getattr(post, "email", ""),
        "phone": getattr(post, "pN", ""),
    }


def _build_dashboard_payload(user):
    labels = []
    approvals = []
    rejections = []
    pending_series = []

    today = datetime.now().date()
    for index in range(28):
        day_start = today - timedelta(days=27 - index)
        day_end = day_start + timedelta(days=1)
        start_datetime = datetime.combine(day_start, datetime.min.time())
        end_datetime = datetime.combine(day_end, datetime.min.time())

        approved_count = Post.objects(created__gte=start_datetime, created__lt=end_datetime, status=1).count()
        rejected_count = Post.objects(created__gte=start_datetime, created__lt=end_datetime, status=0).count()
        pending_count = Post.objects(created__gte=start_datetime, created__lt=end_datetime, status=2).count()

        labels.append(day_start.strftime("%b %d"))
        approvals.append(approved_count)
        rejections.append(rejected_count)
        pending_series.append(pending_count)

    total_reports = Post.objects.count()
    pending_reports_count = Post.objects(status=2).count()
    approved_reports_count = Post.objects(status=1).count()
    rejected_reports_count = Post.objects(status=0).count()
    pending_posts = list(Post.objects(status=2).order_by('-created'))

    return {
        "user": user,
        "wish": wishes(),
        "stats_cards": [
            {"label": "Total Reports", "value": total_reports, "tone": "primary"},
            {"label": "Pending Reports", "value": pending_reports_count, "tone": "warning"},
            {"label": "Approved Reports", "value": approved_reports_count, "tone": "success"},
            {"label": "Rejected Reports", "value": rejected_reports_count, "tone": "danger"},
        ],
        "chart_data": {
            "labels": labels,
            "series": [
                {"name": "Approvals", "data": approvals},
                {"name": "Rejections", "data": rejections},
            ],
            "pending_series": pending_series,
        },
        "pending_reports": [_serialize_pending_post(post) for post in pending_posts],
        "posts": json.loads(Post.objects(status=1).to_json()),
    }


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember = form.cleaned_data.get('remember_me')

            user = authenticate(request, username=username, password=password)

            if not user.is_verified:
                otp_code = random.randint(100000, 999999)
                otp = OTP(username=username, code=otp_code)
                otp.save()
                flag = account_verification_mail(user, otp)
                if flag:
                    messages.success(request, "Please verify your account.")
                    return redirect('superadmin:verification', username=username)
                messages.error(request, "Sorry, Your account is not verified. Try again")

            if user is not None:
                request.session['user_id'] = str(user.id)
                if not remember:
                    request.session.set_expiry(0)
                    response = redirect('superadmin:dashboard')
                    response.delete_cookie('remember_me')
                    response.delete_cookie('user_id')
                    user.is_active = False
                else:
                    request.session.set_expiry(1209600)
                    response = redirect('superadmin:dashboard')
                    response.delete_cookie('remember_me')
                    response.delete_cookie('user_id')
                    response.set_cookie('remember_me', '1', max_age=1209600, httponly=True, samesite='Lax')
                    response.set_cookie('user_id', str(user.id), max_age=1209600, httponly=True, samesite='Lax')

                return response
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

        if request.session.get('user_id'):
            return redirect('superadmin:dashboard')

        if request.COOKIES.get('remember_me') == '1' and request.COOKIES.get('user_id'):
            request.session['user_id'] = request.COOKIES.get('user_id')
            return redirect('superadmin:dashboard')

    return render(request, 'superadmin/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data['username']
            otp_code = random.randint(100000, 999999)
            otp = OTP(username=username, code=otp_code)
            otp.save()
            flag = account_verification_mail(user, otp)
            if flag:
                messages.success(request, "Account created successfully. Please verify your account.")
                return redirect('superadmin:verification', username=username)
            messages.error(request, "Sorry, can't create account. Try again")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'superadmin/createaccount.html', {'form': form})


def account_verification(request, username: str):
    if request.method == 'POST':
        code = request.POST.get("otp")

        try:
            code = int(code)
        except ValueError:
            messages.error(request, "Invalid OTP format.")
            return redirect('superadmin:verification')

        otp_ins = OTP.objects(username=username, code=code).order_by('-created_at').first()

        if otp_ins:
            if otp_ins.expired_at > datetime.utcnow():
                user = User.objects(username=username).first()
                user.is_verified = True
                user.save()
                messages.success(request, "OTP verified successfully.")
                return redirect("superadmin:login")
            messages.error(request, "OTP has expired.")
        else:
            messages.error(request, "OTP has expired.")

    return render(request, "superadmin/accountverification.html")


def unauthorized_view(request):
    return render(request, "superadmin/unauthorized.html")


def dashboard(request):
    if not request.session.get('user_id'):
        return redirect('superadmin:login')

    user_id = request.session.get('user_id')
    user = get_user(user_id)
    if not user:
        return redirect('superadmin:login')
    if not _is_admin_user(user):
        return redirect('superadmin:unauthorized')

    context = _build_dashboard_payload(user)
    return render(request, 'superadmin/dashboard.html', context)


def dashboard_stats_api(request):
    if not request.session.get('user_id'):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    user_id = request.session.get('user_id')
    user = get_user(user_id)
    if not user or not _is_admin_user(user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    payload = _build_dashboard_payload(user)
    return JsonResponse({
        "stats_cards": payload["stats_cards"],
        "chart_data": payload["chart_data"],
        "pending_reports": payload["pending_reports"],
    }, status=200)


def api_accept_post(request, id: str):
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not request.session.get('user_id'):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    user_id = request.session.get('user_id')
    user = get_user(user_id)
    if not user or not _is_admin_user(user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    post = Post.objects(id=ObjectId(id)).first()
    if not post:
        return JsonResponse({"error": "Report not found"}, status=404)

    try:
        if post_mail(post):
            post.status = 1
            post.save()
            payload = _build_dashboard_payload(user)
            return JsonResponse({
                "success": True,
                "message": "Report approved.",
                "stats_cards": payload["stats_cards"],
                "pending_reports": payload["pending_reports"],
            }, status=200)
        return JsonResponse({"error": "Unable to send email to the report creator."}, status=400)
    except Exception as exc:
        return JsonResponse({"error": f"An error occurred: {str(exc)}."}, status=500)


def api_reject_post(request, id: str):
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if not request.session.get('user_id'):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    user_id = request.session.get('user_id')
    user = get_user(user_id)
    if not user or not _is_admin_user(user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    post = Post.objects(id=ObjectId(id)).first()
    if not post:
        return JsonResponse({"error": "Report not found"}, status=404)

    try:
        post.status = 0
        post.save()
        payload = _build_dashboard_payload(user)
        return JsonResponse({
            "success": True,
            "message": "Report rejected.",
            "stats_cards": payload["stats_cards"],
            "pending_reports": payload["pending_reports"],
        }, status=200)
    except Exception as exc:
        return JsonResponse({"error": f"An error occurred: {str(exc)}."}, status=500)


def accept_post(request, id: str):
    next_url = request.GET.get("next", "/")
    if request.method == 'POST':
        return api_accept_post(request, id)

    post = Post.objects(id=ObjectId(id)).first()
    try:
        if post_mail(post):
            post.status = 1
            post.save()
            messages.success(request, "Post has been accepted.")
        else:
            messages.error(request, "Unable to send email to the post creator.")
    except Exception as exc:
        messages.error(request, f"An error occurred: {str(exc)}.")

    return redirect(next_url)


def reject_post(request, id: str):
    next_url = request.GET.get("next", "/")
    if request.method == 'POST':
        return api_reject_post(request, id)

    post = Post.objects(id=ObjectId(id)).first()
    try:
        post.status = 0
        post.save()
        messages.success(request, "Post has been rejected.")
    except Exception as exc:
        messages.error(request, f"An error occurred: {str(exc)}.")

    return redirect(next_url)


def logout_view(request):
    if request.session.get('user_id'):
        user_id = request.session.get('user_id')
        user = get_user(user_id)
        if user:
            user.is_active = False
            user.save()
            del request.session["user_id"]
            request.session.set_expiry(0)
            response = redirect('superadmin:login')
            response.delete_cookie('remember_me')
            response.delete_cookie('user_id')
            return response
    return redirect("superadmin:dashboard")


def forget_password(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")

        otp_code = random.randint(100000, 999999)
        otp = OTP(username=username, code=otp_code)
        otp.save()

        user = User.objects(username=username).first()

        flag = password_reset_mail(user, otp)
        if flag:
            messages.success(request, "We've sent a password reset OTP to your email.")
            return redirect('superadmin:passwordverification', username=username)
        messages.error(request, "Sorry, can't send OTP. Try again")

    return render(request, "superadmin/forgetpassword.html")


def password_verification(request, username: str):
    if request.method == 'POST':
        code = request.POST.get("otp")

        try:
            code = int(code)
        except ValueError:
            messages.error(request, "Invalid OTP format.")
            return redirect('superadmin:verification')

        otp_ins = OTP.objects(username=username, code=code).order_by('-created_at').first()

        if otp_ins:
            if otp_ins.expired_at > datetime.utcnow():
                messages.success(request, "OTP verified successfully.")
                return redirect("superadmin:resetpassword", username=username)
            messages.error(request, "OTP has expired.")
        else:
            messages.error(request, "OTP has expired.")

    return render(request, "superadmin/accountverification.html")


def reset_password(request, username: str):
    if request.method == 'POST':
        password = request.POST.get("password")

        user = User.objects(username=username).first()
        user.password = make_password(password)
        user.save()
        messages.success(request, "Password reset successfully.")

        return redirect("superadmin:login")

    return render(request, "superadmin/resetpassword.html")


def users_view(request):
    superadmins = User.objects(user_type=1)
    admins = User.objects(user_type=2)
    users = User.objects(user_type=3)

    context = {
        "superadmins": superadmins,
        "admins": admins,
        "users": users,
    }

    return render(request, "superadmin/users.html", context)


def user_view(request):
    return render(request, "superadmin/user.html")
