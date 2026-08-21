from typing import TYPE_CHECKING, Any, cast

from django.contrib.auth.models import UserManager as DjangoUserManager

if TYPE_CHECKING:
    from .models import User


class UserManager(DjangoUserManager):
    use_in_migrations = True

    def _create_user(
        self,
        username: str,
        email: str | None,
        password: str | None,
        **extra_fields: Any,
    ) -> "User":
        if not username:
            raise ValueError("El nombre de usuario es obligatorio.")

        is_superuser = bool(extra_fields.get("is_superuser", False))
        created_by = extra_fields.get("created_by")
        if created_by is None and not is_superuser:
            raise ValueError("Un usuario ordinario requiere un actor creador.")

        if created_by is None:
            extra_fields.setdefault(
                "bootstrap_reason",
                "Cuenta técnica inicial creada mediante el comando autorizado.",
            )
        else:
            extra_fields.setdefault("updated_by", created_by)

        username = self.model.normalize_username(username)
        email = self.normalize_email(email)
        user = self.model(username=username, email=email or "", **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return cast("User", user)
