from rest_framework.decorators import api_view, permission_classes ,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import os
import joblib
import numpy as np
from .serializer import RecommendationInputSerializer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, 'trained_model_optimized.pkl')
encoder_path = os.path.join(BASE_DIR, 'label_encoder.pkl')

model = joblib.load(model_path)
label_encoder = joblib.load(encoder_path)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])  # ✅ دي اللي بتخليها مفتوحة من غير أوثنتكيشن
def recommend_department(request):
    print("🔵 Incoming Request Data:", request.data)

    serializer = RecommendationInputSerializer(data=request.data)
    if serializer.is_valid():
        cert = serializer.validated_data['cert']
        tech_skills = serializer.validated_data.get('tech_skills', [])
        subjects = serializer.validated_data.get('subjects', [])
        non_academic = serializer.validated_data.get('non_academic', [])

        features = f"{cert} {' '.join(tech_skills)} {' '.join(subjects)} {' '.join(non_academic)}"
        print("🟡 Combined Features:", features)

        probas = model.predict_proba([features])[0]
        top_indices = np.argsort(probas)[-3:][::-1]
        top_departments = label_encoder.inverse_transform(top_indices)

        response_data = {'recommended_departments': list(top_departments)}
        print("🟢 Response Data:", response_data)

        return Response(response_data, status=status.HTTP_200_OK)
    else:
        print("🔴 Validation Errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
