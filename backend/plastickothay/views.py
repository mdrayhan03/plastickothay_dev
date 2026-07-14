from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from fileupload import upload_to_drive
from plastickothay.models import Post
from superadmin.models import User
from bson import ObjectId
from datetime import datetime, timedelta
import uuid, json
from email_control import post_mail

# https://plastickothay-dev.onrender.com/keep-alive

def keep_alive(request):
    return JsonResponse({"status": "ok"}, status=200)

def get_user(user_id):
    try:
        return User.objects.get(pk=ObjectId(user_id))
    except User.DoesNotExist:
        return None
    except Exception as e:
        return None

def home (request):
    if 'user_id' not in request.session:
        if request.COOKIES.get('remember_me') == '1' and request.COOKIES.get('user_id'):
            request.session['user_id'] = request.COOKIES.get('user_id')

    user = None
    if 'user_id' in request.session:
        try:
            user_id = request.session.get('user_id')
            user = get_user(user_id)
        except:
            user = None       

    if request.method == "POST" :
        name = request.POST.get("nameData")
        phone = request.POST.get("phoneData")
        email = request.POST.get("emailData")
        severity = request.POST.get("severityData")
        photo_data = request.POST.get("photoData")
        lat = request.POST.get("latData")
        lon = request.POST.get("lonData")
        description = request.POST.get("descriptionData") or "No Description"
                
        if photo_data and ';base64,' in photo_data:
            header, base64_data = photo_data.split(';base64,')
            file_ext = header.split('/')[-1]
            filename = f"{uuid.uuid4()}.{file_ext}"
            response = upload_to_drive(photo_data, filename)

        if response :
            post = Post(
                user = user,
                name=name,
                email=email,
                pN=phone,
                severity=severity,
                imageID=response["id"],
                lat=lat,
                lon=lon,
                description=description
            )
            post.save()
            messages.success(request, "Report submitted successfully.")
            return redirect("plastickothay:home")
        else :
            messages.error(request, "Something went wrong.")
            return redirect("plastickothay:home")    

    posts = json.loads(Post.objects(status=1).to_json())
    
    context = {
        "posts" : posts,
        "user" : user,
    }

    return render(request, "plastickothay/index.html", context)

def posts(request):
    if 'user_id' in request.session:
        try:
            user_id = request.session.get('user_id')
            user = get_user(user_id)
        except:
            user = None
    else:
        user = None

    filter_type = request.GET.get('filter', 'all')  # default is 'all'
    now = datetime.now()

    if filter_type == 'today':
        start = datetime(now.year, now.month, now.day)
        posts = Post.objects(created__gte=start).order_by('-created')
    elif filter_type == 'last_week':
        start = now - timedelta(days=7)
        posts = Post.objects(created__gte=start).order_by('-created')
    elif filter_type == 'last_28_days':
        start = now - timedelta(days=28)
        posts = Post.objects(created__gte=start).order_by('-created')
    elif filter_type.startswith('severity_'):
        try:
            sev = int(filter_type.split('_')[1])
            posts = Post.objects(severity=sev).order_by('-created')
        except:
            posts = Post.objects().order_by('-created')
    elif filter_type == 'accepted':
        posts = Post.objects(status=1).order_by('-created')
    elif filter_type == 'pending':
        posts = Post.objects(status=2).order_by('-created')
    else:
        posts = Post.objects().order_by('-created')

    index = request.GET.get("index")

    context = {
        "posts": posts.order_by('-created')[:10],  # First 10 posts for "load more"
        "user": user,
    }
    
    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, "plastickothay/posts.html", context)
    
    return render(request, "plastickothay/posts.html", context)

def post(request, id) :
    if 'user_id' in request.session:
        try:
            user_id = request.session.get('user_id')
            user = get_user(user_id)
        except:
            user = None
    else:
        user = None

    post = Post.objects(id=ObjectId(id)).first()

    if request.method == "POST" :
        description = request.POST.get("description")
        post.description = description
        post.save()
        return redirect("plastickothay:post", id = post.id)

    context = {
        "post" : post,
        "user" : user,
    }

    return render(request, "plastickothay/post.html", context)

def contact(request) :
    return render(request, "plastickothay/contact.html")

def feedback(request) :
    if 'user_id' in request.session:
        try:
            user_id = request.session.get('user_id')
            user = get_user(user_id)
        except:
            user = None
    else:
        user = None
    # print(user)
    context = {
        "user" : user,
    }
    return render(request, "plastickothay/rateus.html", context)

def contribution(request):
    if 'user_id' in request.session:
        try:
            user_id = request.session.get('user_id')
            user = get_user(user_id)
        except:
            user = None
    else:
        user = None
    
    # Calculate user contribution stats
    user_posts = []
    total_points = 0
    photos_posted = 0
    reviews_written = 0
    friends_referred = 0
    current_level = 1
    points_to_next_level = 0
    progress_percentage = 0
    
    if user:
        # Get all accepted posts by user
        user_posts = Post.objects(user=user, status=1)
        photos_posted = user_posts.count()
        
        # Calculate points (each post = 1 point, each review = 1 point, each referral = 1 point)
        total_points = photos_posted + reviews_written + friends_referred
        
        # Calculate level (every 5 points = 1 level)
        current_level = (total_points // 5) + 1
        points_to_next_level = 5 - (total_points % 5)
        
        # Calculate progress percentage for current level (0-100%)
        progress_percentage = min(100, ((total_points % 5) / 5) * 100)
        
        # Get reviews count (assuming reviews are stored separately, for now using 0)
        # reviews_written = Rate.objects(user=user).count() if hasattr(Rate, 'user') else 0
        
        # For demo purposes, set some default values
        reviews_written = 0  # Can be updated when review system is implemented
        friends_referred = 0  # Can be updated when referral system is implemented
    
    # Badge requirements
    badge_requirements = {
        'photos': 2,
        'reviews': 2,
        'referrals': 2
    }
    
    context = {
        "user": user,
        "total_points": total_points,
        "photos_posted": photos_posted,
        "reviews_written": reviews_written,
        "friends_referred": friends_referred,
        "current_level": current_level,
        "points_to_next_level": points_to_next_level,
        "progress_percentage": progress_percentage,
        "badge_requirements": badge_requirements,
        "user_posts": user_posts,
    }
    return render(request, "plastickothay/contribution.html", context)