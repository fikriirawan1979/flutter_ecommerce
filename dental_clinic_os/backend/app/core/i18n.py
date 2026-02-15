"""
Internationalization (i18n) module
"""

from typing import Dict, Optional
from fastapi import Request, Header
from enum import Enum

class SupportedLocale(str, Enum):
    """Supported languages"""
    EN = "en"  # English
    ES = "es"  # Spanish
    FR = "fr"  # French
    DE = "de"  # German
    ZH = "zh"  # Chinese (Simplified)
    AR = "ar"  # Arabic
    PT = "pt"  # Portuguese

# Translation dictionaries
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    SupportedLocale.EN.value: {
        # Auth
        "auth.login_success": "Login successful",
        "auth.login_failed": "Invalid email or password",
        "auth.account_inactive": "Account is deactivated",
        "auth.email_exists": "Email already registered",
        "auth.password_too_weak": "Password is too weak",
        
        # Orders
        "order.created": "Order created successfully",
        "order.paid": "Payment successful",
        "order.failed": "Payment failed",
        "order.refunded": "Order refunded",
        
        # Assessments
        "assessment.created": "Assessment created",
        "assessment.uploaded": "Image uploaded successfully",
        "assessment.analyzed": "Analysis complete",
        "assessment.completed": "Assessment completed",
        
        # Products
        "product.not_found": "Product not found",
        "product.inactive": "Product is not available",
        
        # Users
        "user.not_found": "User not found",
        "user.unauthorized": "Not authorized",
        
        # Tenants
        "tenant.not_found": "Tenant not found",
        "tenant.suspended": "Tenant account suspended",
        "tenant.trial_expired": "Trial period expired",
        
        # General
        "error.server": "Internal server error",
        "error.validation": "Validation error",
        "error.not_found": "Resource not found",
        "error.forbidden": "Access forbidden",
        "error.rate_limit": "Rate limit exceeded",
    },
    
    SupportedLocale.ES.value: {
        # Auth
        "auth.login_success": "Inicio de sesión exitoso",
        "auth.login_failed": "Correo o contraseña inválidos",
        "auth.account_inactive": "Cuenta desactivada",
        "auth.email_exists": "Correo ya registrado",
        "auth.password_too_weak": "Contraseña muy débil",
        
        # Orders
        "order.created": "Orden creada exitosamente",
        "order.paid": "Pago exitoso",
        "order.failed": "Pago fallido",
        "order.refunded": "Orden reembolsada",
        
        # Assessments
        "assessment.created": "Evaluación creada",
        "assessment.uploaded": "Imagen cargada exitosamente",
        "assessment.analyzed": "Análisis completo",
        "assessment.completed": "Evaluación completada",
        
        # Products
        "product.not_found": "Producto no encontrado",
        "product.inactive": "Producto no disponible",
        
        # Users
        "user.not_found": "Usuario no encontrado",
        "user.unauthorized": "No autorizado",
        
        # Tenants
        "tenant.not_found": "Tenant no encontrado",
        "tenant.suspended": "Cuenta de tenant suspendida",
        "tenant.trial_expired": "Período de prueba expirado",
        
        # General
        "error.server": "Error interno del servidor",
        "error.validation": "Error de validación",
        "error.not_found": "Recurso no encontrado",
        "error.forbidden": "Acceso prohibido",
        "error.rate_limit": "Límite de tasa excedido",
    },
    
    SupportedLocale.FR.value: {
        # Auth
        "auth.login_success": "Connexion réussie",
        "auth.login_failed": "Email ou mot de passe invalide",
        "auth.account_inactive": "Compte désactivé",
        "auth.email_exists": "Email déjà enregistré",
        "auth.password_too_weak": "Mot de passe trop faible",
        
        # Orders
        "order.created": "Commande créée avec succès",
        "order.paid": "Paiement réussi",
        "order.failed": "Paiement échoué",
        "order.refunded": "Commande remboursée",
        
        # Assessments
        "assessment.created": "Évaluation créée",
        "assessment.uploaded": "Image téléchargée avec succès",
        "assessment.analyzed": "Analyse terminée",
        "assessment.completed": "Évaluation terminée",
        
        # Products
        "product.not_found": "Produit non trouvé",
        "product.inactive": "Produit non disponible",
        
        # Users
        "user.not_found": "Utilisateur non trouvé",
        "user.unauthorized": "Non autorisé",
        
        # Tenants
        "tenant.not_found": "Tenant non trouvé",
        "tenant.suspended": "Compte tenant suspendu",
        "tenant.trial_expired": "Période d'essai expirée",
        
        # General
        "error.server": "Erreur interne du serveur",
        "error.validation": "Erreur de validation",
        "error.not_found": "Ressource non trouvée",
        "error.forbidden": "Accès interdit",
        "error.rate_limit": "Limite de taux dépassée",
    },
    
    SupportedLocale.DE.value: {
        # Auth
        "auth.login_success": "Login erfolgreich",
        "auth.login_failed": "Ungültige E-Mail oder Passwort",
        "auth.account_inactive": "Konto deaktiviert",
        "auth.email_exists": "E-Mail bereits registriert",
        "auth.password_too_weak": "Passwort zu schwach",
        
        # Orders
        "order.created": "Bestellung erfolgreich erstellt",
        "order.paid": "Zahlung erfolgreich",
        "order.failed": "Zahlung fehlgeschlagen",
        "order.refunded": "Bestellung erstattet",
        
        # Assessments
        "assessment.created": "Bewertung erstellt",
        "assessment.uploaded": "Bild erfolgreich hochgeladen",
        "assessment.analyzed": "Analyse abgeschlossen",
        "assessment.completed": "Bewertung abgeschlossen",
        
        # Products
        "product.not_found": "Produkt nicht gefunden",
        "product.inactive": "Produkt nicht verfügbar",
        
        # Users
        "user.not_found": "Benutzer nicht gefunden",
        "user.unauthorized": "Nicht autorisiert",
        
        # Tenants
        "tenant.not_found": "Tenant nicht gefunden",
        "tenant.suspended": "Tenant-Konto gesperrt",
        "tenant.trial_expired": "Testphase abgelaufen",
        
        # General
        "error.server": "Interner Serverfehler",
        "error.validation": "Validierungsfehler",
        "error.not_found": "Ressource nicht gefunden",
        "error.forbidden": "Zugriff verweigert",
        "error.rate_limit": "Rate-Limit überschritten",
    },
    
    SupportedLocale.ZH.value: {
        # Auth
        "auth.login_success": "登录成功",
        "auth.login_failed": "邮箱或密码无效",
        "auth.account_inactive": "账户已停用",
        "auth.email_exists": "邮箱已注册",
        "auth.password_too_weak": "密码太弱",
        
        # Orders
        "order.created": "订单创建成功",
        "order.paid": "支付成功",
        "order.failed": "支付失败",
        "order.refunded": "订单已退款",
        
        # Assessments
        "assessment.created": "评估已创建",
        "assessment.uploaded": "图片上传成功",
        "assessment.analyzed": "分析完成",
        "assessment.completed": "评估已完成",
        
        # Products
        "product.not_found": "产品未找到",
        "product.inactive": "产品不可用",
        
        # Users
        "user.not_found": "用户未找到",
        "user.unauthorized": "未授权",
        
        # Tenants
        "tenant.not_found": "租户未找到",
        "tenant.suspended": "租户账户已暂停",
        "tenant.trial_expired": "试用期已过期",
        
        # General
        "error.server": "内部服务器错误",
        "error.validation": "验证错误",
        "error.not_found": "资源未找到",
        "error.forbidden": "访问禁止",
        "error.rate_limit": "超过速率限制",
    },
    
    SupportedLocale.AR.value: {
        # Auth (RTL support)
        "auth.login_success": "تسجيل الدخول بنجاح",
        "auth.login_failed": "البريد الإلكتروني أو كلمة المرور غير صالحة",
        "auth.account_inactive": "الحساب معطل",
        "auth.email_exists": "البريد الإلكتروني مسجل بالفعل",
        "auth.password_too_weak": "كلمة المرور ضعيفة جدًا",
        
        # Orders
        "order.created": "تم إنشاء الطلب بنجاح",
        "order.paid": "الدفع ناجح",
        "order.failed": "فشل الدفع",
        "order.refunded": "تم استرداد الطلب",
        
        # Assessments
        "assessment.created": "تم إنشاء التقييم",
        "assessment.uploaded": "تم رفع الصورة بنجاح",
        "assessment.analyzed": "اكتمل التحليل",
        "assessment.completed": "اكتمل التقييم",
        
        # Products
        "product.not_found": "المنتج غير موجود",
        "product.inactive": "المنتج غير متاح",
        
        # Users
        "user.not_found": "المستخدم غير موجود",
        "user.unauthorized": "غير مصرح",
        
        # Tenants
        "tenant.not_found": "المستأجر غير موجود",
        "tenant.suspended": "حساب المستأجر معلق",
        "tenant.trial_expired": "انتهت الفترة التجريبية",
        
        # General
        "error.server": "خطأ في الخادم الداخلي",
        "error.validation": "خطأ في التحقق",
        "error.not_found": "المورد غير موجود",
        "error.forbidden": "الوصول محظور",
        "error.rate_limit": "تجاوز حد المعدل",
    },
    
    SupportedLocale.PT.value: {
        # Auth
        "auth.login_success": "Login bem-sucedido",
        "auth.login_failed": "Email ou senha inválidos",
        "auth.account_inactive": "Conta desativada",
        "auth.email_exists": "Email já registrado",
        "auth.password_too_weak": "Senha muito fraca",
        
        # Orders
        "order.created": "Pedido criado com sucesso",
        "order.paid": "Pagamento bem-sucedido",
        "order.failed": "Pagamento falhou",
        "order.refunded": "Pedido reembolsado",
        
        # Assessments
        "assessment.created": "Avaliação criada",
        "assessment.uploaded": "Imagem carregada com sucesso",
        "assessment.analyzed": "Análise concluída",
        "assessment.completed": "Avaliação concluída",
        
        # Products
        "product.not_found": "Produto não encontrado",
        "product.inactive": "Produto não disponível",
        
        # Users
        "user.not_found": "Usuário não encontrado",
        "user.unauthorized": "Não autorizado",
        
        # Tenants
        "tenant.not_found": "Tenant não encontrado",
        "tenant.suspended": "Conta tenant suspensa",
        "tenant.trial_expired": "Período de teste expirado",
        
        # General
        "error.server": "Erro interno do servidor",
        "error.validation": "Erro de validação",
        "error.not_found": "Recurso não encontrado",
        "error.forbidden": "Acesso proibido",
        "error.rate_limit": "Limite de taxa excedido",
    },
}


def get_locale(
    accept_language: Optional[str] = Header(None)
) -> SupportedLocale:
    """
    Determine the locale from Accept-Language header
    Defaults to English if not specified or not supported
    """
    if not accept_language:
        return SupportedLocale.EN
    
    # Parse Accept-Language header
    # Format: "en-US,en;q=0.9,es;q=0.8"
    locales = []
    for part in accept_language.split(","):
        if ";" in part:
            locale, q = part.split(";")
        else:
            locale = part
            q = "1.0"
        
        # Extract language code (before hyphen)
        lang_code = locale.split("-")[0].strip().lower()
        q_value = float(q.split("=")[1].strip()) if "=" in q else 1.0
        locales.append((lang_code, q_value))
    
    # Sort by quality value
    locales.sort(key=lambda x: -x[1])
    
    # Find first supported locale
    for lang_code, _ in locales:
        try:
            return SupportedLocale(lang_code)
        except ValueError:
            continue
    
    return SupportedLocale.EN


def translate(key: str, locale: SupportedLocale = SupportedLocale.EN) -> str:
    """
    Get translated string for a key
    
    Args:
        key: Translation key (e.g., "auth.login_success")
        locale: Target locale
        
    Returns:
        Translated string or the key itself if not found
    """
    locale_str = locale.value if isinstance(locale, SupportedLocale) else locale
    
    translations = TRANSLATIONS.get(locale_str, TRANSLATIONS[SupportedLocale.EN.value])
    return translations.get(key, key)


def t(key: str, request: Request) -> str:
    """
    Convenience function to translate using request's locale
    
    Args:
        key: Translation key
        request: FastAPI request object
        
    Returns:
        Translated string
    """
    # Get locale from request state (set by middleware)
    locale = getattr(request.state, "locale", SupportedLocale.EN)
    return translate(key, locale)


class LocaleMiddleware:
    """
    Middleware to detect and set locale from request
    """
    
    async def __call__(self, request: Request, call_next):
        # Get locale from Accept-Language header
        accept_language = request.headers.get("accept-language", "")
        locale = get_locale(accept_language)
        
        # Store in request state
        request.state.locale = locale
        
        response = await call_next(request)
        
        # Add locale to response headers
        response.headers["Content-Language"] = locale.value
        
        return response


# Dependency to get locale in endpoints
def get_current_locale(request: Request) -> SupportedLocale:
    """Get current locale from request"""
    return getattr(request.state, "locale", SupportedLocale.EN)
