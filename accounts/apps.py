from django.apps import AppConfig

class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        import accounts.signals  # هذا سيقوم بتحميل السيجنالات عند بدء التطبيق
