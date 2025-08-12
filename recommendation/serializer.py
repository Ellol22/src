from rest_framework import serializers

class RecommendationInputSerializer(serializers.Serializer):
    cert = serializers.ChoiceField(choices=[
        "ثانوية عامة (علمي رياضة)", 
        "دبلوم فني صناعي (3 سنوات)", 
        "دبلوم فني صناعي (5 سنوات)", 
        "مدرسة تكنولوجيا تطبيقية", 
        "أخرى"
    ])
    tech_skills = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False
    )
    subjects = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False
    )
    non_academic = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False
    )
