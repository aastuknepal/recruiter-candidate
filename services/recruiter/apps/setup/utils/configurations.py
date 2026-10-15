from apps.setup.models import Configuration


class ConfigService:
    @staticmethod
    def get(key, default=None):
        try:
            config = Configuration.objects.get(config_key=key)
        except Configuration.DoesNotExist:
            return default

        if config.config_type == "number":
            return int(config.value)

        if config.config_type == "boolean":
            return str(config.value).lower() == "true"

        return config.value
