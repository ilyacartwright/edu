from .models import SiteSettings

def site_settings(request):
    """
    Добавляет настройки сайта в контекст шаблонов
    """
    return {
        'site_settings': SiteSettings.get_settings(),
    }

