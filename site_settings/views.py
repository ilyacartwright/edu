from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from .models import SiteSettings
from django.contrib.auth.decorators import login_required
from accounts.utils import get_nested_field_value


@require_GET
def favicon_view(request):
    """
    Представление для отдачи favicon
    """
    site_settings = SiteSettings.get_settings()
    
    if site_settings.site_favicon:
        return HttpResponseRedirect(site_settings.site_favicon.url)
    
    # Возвращаем стандартный favicon, если он не настроен
    return HttpResponseRedirect('/static/img/favicon.ico')

