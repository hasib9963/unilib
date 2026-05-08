# Home App

The home app handles the landing page and home page functionality for the UniLib library management system.

## Features

### Landing Page
- Welcome message and library introduction
- Quick access to main features
- Featured books or announcements
- Authentication status display
- Navigation to main sections

### Home Page
- User-specific content based on authentication status
- Quick links to common actions
- Library statistics overview
- Recent activity highlights
- Search functionality integration

## Views

### Home Views
- `home`: Main home page view
  - Displays different content for authenticated vs. anonymous users
  - Shows quick action links
  - Displays library statistics
  - Provides navigation to main features

## URL Patterns

```
/    # Home page (root URL)
```

## Templates

- `home/home.html`: Main home page template

## Template Structure

### For Anonymous Users
- Welcome message
- Call-to-action for registration/login
- Library features overview
- Search bar (if enabled for public)
- Contact information

### For Authenticated Users
- Personalized greeting
- Quick action links based on role
- Recent activity summary
- Notification preview
- Dashboard shortcut

## Usage Examples

### Home View Logic
```python
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home(request):
    context = {
        'user': request.user,
        'is_authenticated': request.user.is_authenticated,
    }
    
    if request.user.is_authenticated:
        # Add user-specific context
        context['active_borrows'] = request.user.get_active_borrows()
        context['overdue_borrows'] = request.user.get_overdue_borrows()
    
    return render(request, 'home/home.html', context)
```

### Template Example
```html
{% extends "base.html" %}

{% block content %}
<div class="home-container">
    {% if user.is_authenticated %}
        <h1>Welcome back, {{ user.get_full_name }}!</h1>
        <div class="quick-links">
            <a href="{% url 'dashboard' %}">Dashboard</a>
            <a href="{% url 'book_list' %}">Browse Books</a>
            <a href="{% url 'profile' %}">My Profile</a>
        </div>
    {% else %}
        <h1>Welcome to UniLib</h1>
        <p>Your university library management system</p>
        <div class="auth-links">
            <a href="{% url 'login' %}">Login</a>
            <a href="{% url 'register' %}">Register</a>
        </div>
    {% endif %}
</div>
{% endblock %}
```

## Integration with Other Apps

- **Accounts**: Authentication status and user information
- **Books**: Featured books display
- **Dashboard**: Quick link to user dashboard
- **Notifications**: Notification preview for authenticated users

## Customization Options

### Static Content
- Welcome messages
- Library information
- Feature descriptions
- Contact information

### Dynamic Content
- User-specific greetings
- Role-based quick links
- Statistics overview
- Recent activity

### Styling
- Hero section design
- Feature cards
- Quick link buttons
- Responsive layout

## Future Enhancements

- Featured books carousel
- Library news and announcements
- Upcoming events display
- Library hours and information
- Virtual tour integration
- Search functionality on home page
- Popular books section
- New arrivals display
- Library statistics visualization
- Multi-language support
- Customizable home page layout