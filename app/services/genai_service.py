"""Google Gen AI service for the Interior AI Service."""

import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from google import genai
from google.genai import types

from app.config import get_settings
from app.models.client_data import ClientFormData
from app.models.client_profile import ClientProfile, DesignRecommendation
from app.utils.errors import GenAIServiceError, handle_service_error
from app.utils.logging import log_ai_interaction, timed_operation, StructuredLogger

logger = StructuredLogger("genai_service")


class GenAIService:
    """Google Gen AI service for generating client profiles."""
    
    def __init__(self):
        self.settings = get_settings()
        self.model_name = self.settings.genai_model
        self.location = self.settings.vertex_ai_location
        self.project_id = self.settings.google_cloud_project
        self._initialize_genai()
        logger.info(
            f"🤖 GenAI Service initialized",
            model=self.model_name,
            location=self.location,
            project_id=self.project_id
        )
    
    def _initialize_genai(self) -> None:
        """Initialize Google Gen AI client."""
        try:
            self.genai_client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location
            )
            logger.info(f"✅ Google Gen AI initialized with model: {self.model_name}")
        except Exception as e:
            raise GenAIServiceError(
                f"Failed to initialize Google Gen AI: {str(e)}",
                model_used=self.model_name
            )
    
    def generate_client_profile(self, client_data: ClientFormData) -> ClientProfile:
        """Generate a complete client profile using AI."""
        with timed_operation("generate_client_profile", client_name=client_data.client_name):
            try:
                prompt = self._create_profile_prompt(client_data)
                response = self._generate_ai_response(prompt)
                profile = self._parse_profile_response(response, client_data)
                logger.info(
                    f"✅ Client profile generated successfully",
                    client_name=client_data.client_name,
                    project_type=client_data.project_type,
                    recommendations_count=len(profile.recommendations)
                )
                return profile
            except Exception as e:
                handle_service_error(
                    e, "GenAI", "generate_client_profile",
                    context={"client_name": client_data.client_name}
                )
    
    def _create_profile_prompt(self, client_data: ClientFormData) -> str:
        context = client_data.to_genai_context()
        prompt = f"""
You are an expert interior designer with 15+ years of experience. Analyze the following client information and create a comprehensive interior design profile.

CLIENT INFORMATION:
{context}

Please provide a detailed analysis in the following JSON format:

{{
    "client_name": "Client's full name",
    "email": "Client's email address",
    "phone": "Client's phone number (if provided)",
    "project_type": "Type of interior design project",
    "project_summary": "2-3 sentence summary of the project",
    "property_address": "Property address (if provided)",
    "room_count": "Number of rooms (if provided)",
    "square_feet": "Property size (if provided)",
    "budget_range": "Budget range (if provided)",
    "timeline": "Project timeline (if provided)",
    "style_preference": "Design style preference (if provided)",
    "urgency": "Project urgency level (if provided)",
    "design_style_analysis": "Detailed analysis of client's style preferences and how they align with current trends",
    "space_analysis": "Analysis of the space, its potential, and key considerations",
    "budget_analysis": "Analysis of budget considerations and recommendations",
    "timeline_analysis": "Analysis of timeline and project planning considerations",
    "recommendations": [
        {{
            "category": "Category (e.g., 'Color Scheme', 'Furniture', 'Layout', 'Lighting', 'Materials')",
            "title": "Short title for the recommendation",
            "description": "Detailed description of the recommendation",
            "reasoning": "AI reasoning behind this recommendation",
            "priority": "Priority level (low, medium, high)",
            "estimated_cost": "Estimated cost range (e.g., '$500-1500')",
            "timeline": "Estimated timeline for implementation (e.g., '1-2 weeks')"
        }}
    ],
    "overall_recommendation": "Overall design recommendation summary (2-3 paragraphs)",
    "next_steps": [
        "Specific next step 1",
        "Specific next step 2",
        "Specific next step 3"
    ],
    "estimated_project_duration": "Estimated total project duration (e.g., '8-12 weeks')",
    "estimated_total_cost": "Estimated total project cost range (e.g., '$15,000-25,000')"
}}

IMPORTANT GUIDELINES:
1. Provide 3-5 specific design recommendations based on the client's information
2. Be realistic about costs and timelines
3. Consider the client's budget and timeline constraints
4. Provide actionable next steps
5. Ensure all recommendations are practical and implementable
6. If information is missing, make reasonable assumptions and note them
7. Focus on creating a cohesive, functional, and beautiful design
8. Consider sustainability and long-term value

Please respond with only the JSON object, no additional text.
"""
        return prompt
    
    def _generate_ai_response(self, prompt: str) -> str:
        """Generate AI response using Google Gen AI."""
        start_time = time.time()
        try:
            response = self.genai_client.models.generate_content(
                model=self.model_name,
                contents=[types.Content(
                    parts=[types.Part(text=prompt)],
                    role="user"
                )],
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=8192,
                )
            )
            response_text = response.candidates[0].content.parts[0].text
            duration = time.time() - start_time
            log_ai_interaction(
                model=self.model_name,
                prompt_length=len(prompt),
                response_length=len(response_text),
                duration_seconds=duration,
                success=True
            )
            return response_text
        except Exception as e:
            duration = time.time() - start_time
            log_ai_interaction(
                model=self.model_name,
                prompt_length=len(prompt),
                response_length=0,
                duration_seconds=duration,
                success=False,
                error=str(e)
            )
            raise GenAIServiceError(
                f"Failed to generate AI response: {str(e)}",
                model_used=self.model_name,
                prompt_length=len(prompt),
                response_time=duration
            )
    
    def _parse_profile_response(self, response: str, client_data: ClientFormData) -> ClientProfile:
        try:
            cleaned_response = self._clean_ai_response(response)
            profile_data = json.loads(cleaned_response)
            recommendations = []
            for rec_data in profile_data.get("recommendations", []):
                recommendation = DesignRecommendation(
                    category=rec_data.get("category", "General"),
                    title=rec_data.get("title", "Design Recommendation"),
                    description=rec_data.get("description", ""),
                    reasoning=rec_data.get("reasoning", ""),
                    priority=rec_data.get("priority", "medium"),
                    estimated_cost=rec_data.get("estimated_cost"),
                    timeline=rec_data.get("timeline")
                )
                recommendations.append(recommendation)
            original_data_summary = {
                "field_count": len(client_data.raw_data),
                "quality_score": client_data.raw_data.get("quality_score", 0.0),
                "processed_fields": list(client_data.raw_data.keys())
            }
            # Convert numeric values to strings for fields that expect strings
            room_count = profile_data.get("room_count", client_data.room_count)
            if room_count is not None:
                room_count = str(room_count)
            
            square_feet = profile_data.get("square_feet", client_data.square_feet)
            if square_feet is not None:
                square_feet = str(square_feet)
            
            profile = ClientProfile(
                client_name=profile_data.get("client_name", client_data.client_name or "Unknown"),
                email=profile_data.get("email", client_data.email or ""),
                phone=profile_data.get("phone", client_data.phone),
                project_type=profile_data.get("project_type", client_data.project_type or "Interior Design"),
                project_summary=profile_data.get("project_summary", ""),
                property_address=profile_data.get("property_address", client_data.address),
                room_count=room_count,
                square_feet=square_feet,
                budget_range=profile_data.get("budget_range", client_data.budget_range),
                timeline=profile_data.get("timeline", client_data.timeline),
                style_preference=profile_data.get("style_preference", client_data.style_preference),
                urgency=profile_data.get("urgency", client_data.urgency),
                design_style_analysis=profile_data.get("design_style_analysis", ""),
                space_analysis=profile_data.get("space_analysis", ""),
                budget_analysis=profile_data.get("budget_analysis", ""),
                timeline_analysis=profile_data.get("timeline_analysis", ""),
                recommendations=recommendations,
                overall_recommendation=profile_data.get("overall_recommendation", ""),
                next_steps=profile_data.get("next_steps", []),
                estimated_project_duration=profile_data.get("estimated_project_duration"),
                estimated_total_cost=profile_data.get("estimated_total_cost"),
                ai_model_used=self.model_name,
                original_data_summary=original_data_summary
            )
            return profile
        except json.JSONDecodeError as e:
            raise GenAIServiceError(
                f"Failed to parse AI response as JSON: {str(e)}",
                model_used=self.model_name,
                response_preview=response[:200]
            )
        except Exception as e:
            raise GenAIServiceError(
                f"Failed to parse profile response: {str(e)}",
                model_used=self.model_name
            )
    
    def _clean_ai_response(self, response: str) -> str:
        if response.startswith("```json"):
            response = response[7:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        start_idx = response.find("{")
        end_idx = response.rfind("}")
        if start_idx != -1 and end_idx != -1:
            response = response[start_idx:end_idx + 1]
        return response
    
    def test_connection(self) -> Dict[str, Any]:
        try:
            with timed_operation("test_genai_connection"):
                test_prompt = "Respond with 'OK' if you can read this message."
                response = self._generate_ai_response(test_prompt)
                return {
                    "status": "connected",
                    "model": self.model_name,
                    "response": response.strip(),
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "model": self.model_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


_genai_service_instance = None

def get_genai_service() -> GenAIService:
    global _genai_service_instance
    if _genai_service_instance is None:
        _genai_service_instance = GenAIService()
    return _genai_service_instance
