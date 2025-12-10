import yookassa
from yookassa import Payment, Configuration
from datetime import datetime
import uuid
import logging
from config import Config
from database import db

logger = logging.getLogger(__name__)

# Настройка Яндекс Кассы
Configuration.account_id = Config.YOOKASSA_SHOP_ID
Configuration.secret_key = Config.YOOKASSA_SECRET_KEY

class YooKassaPayment:
    @staticmethod
    async def create_payment(user_id: int, plan_key: str, telegram_id: int) -> dict:
        """Создание платежа в Яндекс Кассе"""
        try:
            plan = Config.SUBSCRIPTION_PLANS.get(plan_key)
            if not plan:
                return {'success': False, 'error': 'Тарифный план не найден'}
            
            # Генерируем уникальный ID платежа
            payment_id = str(uuid.uuid4())
            
            # Создаем описание платежа
            description = f"Подписка на {plan['name']} для пользователя {telegram_id}"
            
            # Вариант 1: Используем email из конфига
            receipt = {
                "customer": {
                    "email": Config.DEFAULT_EMAIL,
                    "full_name": f"Пользователь Telegram ID: {telegram_id}"
                },
                "items": [
                    {
                        "description": description[:128],  # Максимум 128 символов
                        "quantity": "1.00",
                        "amount": {
                            "value": str(plan['price']),
                            "currency": "RUB"
                        },
                        "vat_code": Config.VAT_CODE,  # Используем из конфига
                        "payment_mode": "full_payment",
                        "payment_subject": "service"
                    }
                ]
            }
            
            # Вариант 2: Если нет email, используем тестовый
            if not Config.DEFAULT_EMAIL or Config.DEFAULT_EMAIL == "user@example.com":
                receipt["customer"] = {
                    "email": f"user{telegram_id}@example.com",
                    "full_name": f"Пользователь Telegram ID: {telegram_id}"
                }
            
            # Создаем платеж в Яндекс Кассе
            payment_data = {
                "amount": {
                    "value": str(plan['price']),
                    "currency": "RUB"
                },
                "payment_method_data": {
                    "type": "bank_card"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": Config.YOOKASSA_RETURN_URL or f"https://t.me/{Config.BOT_USERNAME}"
                },
                "capture": True,
                "description": description,
                "metadata": {
                    "user_id": user_id,
                    "telegram_id": telegram_id,
                    "plan_key": plan_key,
                    "plan_name": plan['name']
                },
                "receipt": receipt
            }
            
            # Если указана налоговая система в конфиге
            if hasattr(Config, 'TAX_SYSTEM_CODE') and Config.TAX_SYSTEM_CODE:
                payment_data["tax_system_code"] = Config.TAX_SYSTEM_CODE
            
            payment = Payment.create(payment_data)
            
            # Сохраняем платеж в БД
            await db.create_payment_record(
                user_id=user_id,
                payment_id=payment.id,
                amount=float(plan['price']),
                plan_key=plan_key
            )
            
            return {
                'success': True,
                'payment_id': payment.id,
                'confirmation_url': payment.confirmation.confirmation_url,
                'amount': plan['price'],
                'plan_name': plan['name']
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания платежа: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    async def check_payment_status(payment_id: str) -> dict:
        """Проверка статуса платежа"""
        try:
            payment = Payment.find_one(payment_id)
            
            # Если платеж успешен, активируем подписку
            if payment.status == 'succeeded':
                metadata = payment.metadata
                if metadata:
                    user_id = metadata.get('user_id')
                    plan_key = metadata.get('plan_key')
                    if user_id and plan_key:
                        # Активируем подписку
                        await db.create_subscription(user_id, plan_key, payment_id)
            
            return {
                'success': True,
                'status': payment.status,
                'paid': payment.paid,
                'amount': payment.amount.value,
                'metadata': payment.metadata
            }
        except Exception as e:
            logger.error(f"Ошибка проверки статуса платежа: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    async def handle_webhook(data: dict) -> dict:
        """Обработка вебхука от Яндекс Кассы"""
        try:
            event = data.get('event')
            payment_data = data.get('object', {})
            payment_id = payment_data.get('id')
            
            if event == 'payment.succeeded':
                # Обновляем статус платежа в БД
                await db.update_payment_status(payment_id, 'succeeded')
                
                # Получаем метаданные для активации подписки
                metadata = payment_data.get('metadata', {})
                user_id = metadata.get('user_id')
                plan_key = metadata.get('plan_key')
                
                if user_id and plan_key:
                    # Активируем подписку
                    await db.create_subscription(user_id, plan_key, payment_id)
                
                return {'success': True, 'message': 'Payment succeeded and subscription activated'}
            
            elif event == 'payment.waiting_for_capture':
                await db.update_payment_status(payment_id, 'pending')
                return {'success': True, 'message': 'Payment pending capture'}
            
            elif event == 'payment.canceled':
                await db.update_payment_status(payment_id, 'failed')
                return {'success': True, 'message': 'Payment canceled'}
            
            elif event == 'payment.refund.succeeded':
                await db.update_payment_status(payment_id, 'refunded')
                return {'success': True, 'message': 'Payment refunded'}
            
            return {'success': False, 'error': 'Unknown event'}
        except Exception as e:
            logger.error(f"Ошибка обработки вебхука: {e}")
            return {'success': False, 'error': str(e)}