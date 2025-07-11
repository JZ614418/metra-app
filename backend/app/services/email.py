"""
Email service using Resend API
"""
import resend
from typing import List, Optional
from app.core.config import settings

# Initialize Resend with API key
resend.api_key = settings.RESEND_API_KEY


class EmailService:
    @staticmethod
    async def send_welcome_email(to_email: str, user_name: str) -> bool:
        """Send welcome email to new user"""
        try:
            response = resend.Emails.send({
                "from": "Metra <onboarding@metratraining.com>",
                "to": [to_email],
                "subject": "Welcome to Metra - Your Language Model Training Platform",
                "html": f"""
                <h2>Welcome to Metra, {user_name}!</h2>
                <p>Thank you for joining Metra, the platform that makes training custom language models simple.</p>
                <p>With Metra, you can:</p>
                <ul>
                    <li>🎯 Define NLP tasks in plain English</li>
                    <li>🤖 Get AI-recommended language models</li>
                    <li>📊 Collect and prepare text data effortlessly</li>
                    <li>🚀 Fine-tune models without coding</li>
                    <li>🌐 Deploy your models as APIs</li>
                </ul>
                <p>Get started by creating your first language model project!</p>
                <br>
                <p>Best regards,<br>The Metra Team</p>
                """
            })
            return response["id"] is not None
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
            return False

    @staticmethod
    async def send_password_reset_email(to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        try:
            reset_link = f"https://metratraining.com/reset-password?token={reset_token}"
            
            response = resend.Emails.send({
                "from": "Metra <security@metratraining.com>",
                "to": [to_email],
                "subject": "Reset Your Metra Password",
                "html": f"""
                <h2>Password Reset Request</h2>
                <p>We received a request to reset your password for your Metra account.</p>
                <p>Click the link below to reset your password:</p>
                <p><a href="{reset_link}" style="background-color: #111827; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a></p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
                <br>
                <p>Best regards,<br>The Metra Team</p>
                """
            })
            return response["id"] is not None
        except Exception as e:
            print(f"Failed to send password reset email: {e}")
            return False

    @staticmethod
    async def send_training_complete_email(
        to_email: str, 
        user_name: str,
        model_name: str,
        accuracy: float,
        training_time: str
    ) -> bool:
        """Send email when model training is complete"""
        try:
            response = resend.Emails.send({
                "from": "Metra <notifications@metratraining.com>",
                "to": [to_email],
                "subject": f"Your model '{model_name}' is ready!",
                "html": f"""
                <h2>Training Complete! 🎉</h2>
                <p>Hi {user_name},</p>
                <p>Great news! Your language model <strong>{model_name}</strong> has finished training.</p>
                <h3>Training Results:</h3>
                <ul>
                    <li>📊 Accuracy: {accuracy:.2%}</li>
                    <li>⏱️ Training Time: {training_time}</li>
                    <li>✅ Status: Ready for deployment</li>
                </ul>
                <p>You can now:</p>
                <ul>
                    <li>Test your model with sample inputs</li>
                    <li>Deploy it as an API</li>
                    <li>Export it for local use</li>
                </ul>
                <p><a href="https://metratraining.com/dashboard" style="background-color: #111827; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">View Your Model</a></p>
                <br>
                <p>Happy modeling!<br>The Metra Team</p>
                """
            })
            return response["id"] is not None
        except Exception as e:
            print(f"Failed to send training complete email: {e}")
            return False


# Create a singleton instance
email_service = EmailService() 