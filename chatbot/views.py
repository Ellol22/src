import json
import logging
import random
import re
from fuzzywuzzy import fuzz
from ar_corrector.corrector import Corrector
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatBot:
    def __init__(self, data_file='converted_intents.json'):
        """
        تهيئة الشات بوت بتحميل ملف الـ intents وإعداد أداة تصحيح الأخطاء الإملائية.
        """
        # تحميل ملف الـ intents
        try:
            with open(data_file, 'r', encoding='utf-8') as file:
                self.intents = json.load(file)['intents']
        except FileNotFoundError:
            logging.error(f"ملف {data_file} غير موجود.")
            raise FileNotFoundError(f"ملف {data_file} غير موجود. تأكد من وجود الملف في نفس المجلد.")

        # باقي الكود كما هو...
        # تهيئة أداة تصحيح الأخطاء الإملائية
        try:
            self.corrector = Corrector()
            logging.info("تم تهيئة أداة تصحيح الأخطاء الإملائية بنجاح.")
        except Exception as e:
            logging.error(f"فشل في تهيئة Corrector: {str(e)}")
            raise

        # معجم العبارات المعادلة
        self.phrases_equivalent = {
            "ما هو اسم الكلية بالتحديد؟": [
                "اسم الكلية ايه؟", "ايه اسم الكلية؟", "الكلية اسمها ايه؟", "بتسمي الكلية ايه؟",
                "اسم الكلية بالظبط؟", "ايه الكلية دي؟", "الكلية اسمها ايه بالضبط؟", "اسم الكلية كامل؟"
            ],
            "هل الكلية معتمدة من وزارة التعليم العالي؟": [
                "الكلية معتمدة؟", "وزارة التعليم معترفة بالكلية؟", "الكلية رسمية؟", "معتمدة من الوزارة؟",
                "الكلية قانونية؟", "الكلية معترف بيها؟", "وزارة التعليم بتعترف بيها؟", "هي معتمدة رسمي؟"
            ],
            "ما هي مدة الدراسة؟": [
                "مدة الدراسة كام؟", "كم سنة الدراسة؟", "الدراسة بتاخد قد ايه؟", "مدة الدراسة ايه؟",
                "الدراسة كام سنة؟", "قد ايه بتدرس؟", "الدراسة بتستمر كام؟", "مدة الدراسة كام سنة؟",
                "كم مدة الدراسة؟", "الدراسة بتخلّص في كام سنة؟"
            ],
            "أين يقع المقر الرئيسي؟": [
                "المقر فين؟", "الكلية فين؟", "عنوان الكلية ايه؟", "المبنى الرئيسي فين؟",
                "الكلية موجودة فين؟", "فين مكان الكلية؟", "عنوان الكلية بالظبط؟", "الكلية في أي حي؟",
                "المقر الرئيسي فين؟", "فين الكلية في القاهرة؟"
            ],
            "هل الكلية لها فروع أخرى؟": [
                "في فروع تانية؟", "الكلية ليها فروع؟", "في أماكن تانية للكلية؟", "في فروع غير القاهرة؟",
                "الكلية عندها فروع تاني؟", "في فروع في محافظات تانية؟", "الكلية ليها فروع برا القاهرة؟",
                "في فروع أخرى للكلية؟"
            ],
            "ما هي الأقسام المتاحة؟": [
                "ايه الاقسام؟", "التخصصات ايه؟", "في ايه تخصصات؟", "الأقسام اللي موجودة ايه؟",
                "ايه الأقسام اللي في الكلية؟", "التخصصات المتاحة ايه؟", "في ايه أقسام؟",
                "الكلية فيها ايه تخصصات؟", "ايه البرامج الدراسية؟", "التخصصات اللي بتدرسوها ايه؟"
            ],
            "هل يوجد قسم للطاقة المتجددة؟": [
                "في قسم طاقة؟", "الطاقة المتجددة موجودة؟", "قسم الطاقة موجود؟", "في تخصص طاقة متجددة؟",
                "الطاقة الخضراء موجودة؟", "في قسم للطاقة المتجددة؟", "بتدرسوا طاقة متجددة؟",
                "في تخصص طاقة شمسية؟"
            ],
            "ما هو أكثر قسم مطلوب في سوق العمل؟": [
                "ايه التخصص المطلوب؟", "اكتر قسم شغل ايه؟", "ايه القسم اللي عليه طلب؟",
                "ايه التخصصات اللي ليها مستقبل؟", "اكتر قسم مطلوب ايه؟", "ايه التخصص اللي بيشتغل بسرعة؟",
                "سوق العمل محتاج ايه؟", "ايه القسم اللي عليه طلب كبير؟"
            ],
            "هل يمكن الجمع بين تخصصين؟": [
                "اقدر أدمج تخصصين؟", "في دمج تخصصات؟", "ينفع أخد تخصصين؟", "ممكن أجمع تخصصين؟",
                "في دراسة تخصصين مع بعض؟", "اقدر أدرس تخصصين؟", "ينفع تخصصين مع بعض؟",
                "في دبلومة بتجمع تخصصين؟"
            ],
            "ما هو الفرق بين الميكاترونكس والأوتوترونكس؟": [
                "ايه فرق الميكاترونكس والأوتوترونكس؟", "الميكاترونكس غير الأوتوترونكس؟",
                "الفرق بينهم ايه؟", "ايه اللي يميز كل قسم؟", "الميكاترونكس والأوتوترونكس ايه الفرق؟",
                "ايه الفرق بين القسمين؟", "الميكاترونكس بيختلف ازاي؟"
            ],
            "ما هي شروط القبول؟": [
                "شروط الالتحاق ايه؟", "ايه شروط القبول؟", "عايز اعرف شروط التقديم", "ازاي اقبل في الكلية؟",
                "شروط الدخول ايه؟", "ايه اللي مطلوب عشان أقدم؟", "شروط التسجيل ايه؟",
                "القبول عايز ايه؟"
            ],
            "هل هناك قبول للمعدلات المنخفضة؟": [
                "ينفع معدل قليل؟", "المعدلات الضعيفة تتقبل؟", "في قبول لمعدلات نازلة؟",
                "لو معدلي مش عالي اقدر أقدم؟", "المعدلات القليلة تتاخد؟", "في قبول للمعدل المنخفض؟",
                "لو درجاتي مش قوية اقدر أقدم؟", "المعدل الضعيف ينفع؟"
            ],
            "كيف أتقدم بطلب التحاق؟": [
                "ازاي اقدم؟", "طريقة التقديم ايه؟", "اقدم ازاي؟", "ازاي أسجل في الكلية؟",
                "خطوات التقديم ايه؟", "ازاي أقدم طلب؟", "طريقة التسجيل ايه؟", "اقدر أقدم ازاي؟"
            ],
            "ما هي رسوم التقديم؟": [
                "تكلفة التقديم كام؟", "رسوم التقديم ايه؟", "التقديم بكام؟", "بتدفع كام عشان تقدم؟",
                "رسوم التسجيل كام؟", "التقديم تكلفته كام؟", "رسوم الطلب كام؟", "بدفع كام عشان أسجل؟"
            ],
            "هل يمكن التقديم بعد انتهاء الموعد؟": [
                "ينفع اقدم بعد الميعاد؟", "التقديم مفتوح بعد الموعد؟", "لو فات الميعاد اقدر اقدم؟",
                "في تقديم متأخر؟", "لو الموعد خلّص اقدر أقدم؟", "اقدر أسجل بعد الميعاد؟",
                "في فرصة للتقديم بعد الموعد؟"
            ],
            "هل يوجد تدريب عملي في الكلية؟": [
                "في تدريب عملي؟", "بتدربوا في ورش؟", "في تدريب في معامل؟", "الدراسة فيها عملي؟",
                "في تطبيق عملي؟", "بتعملوا تدريب في المعامل؟", "في ورش عمل؟", "التدريب عملي موجود؟"
            ],
            "ما هي مدة برنامج الدبلوم؟": [
                "الدبلوم كام سنة؟", "مدة الدبلوم ايه؟", "كم مدة الدبلوم؟", "الدبلوم بياخد قد ايه؟",
                "قد ايه الدبلوم؟", "الدبلوم بيستمر كام؟", "مدة دراسة الدبلوم كام؟",
                "الدبلوم كام سنة دراسة؟"
            ],
            "ما هي مدة برنامج البكالوريوس؟": [
                "البكالوريوس كام سنة؟", "مدة البكالوريوس ايه؟", "كم مدة البكالوريوس؟",
                "البكالوريوس بياخد قد ايه؟", "قد ايه البكالوريوس؟", "البكالوريوس بيستمر كام؟",
                "مدة دراسة البكالوريوس كام؟", "البكالوريوس كام سنة دراسة؟"
            ],
            "هل يمكن التحويل من كلية أخرى؟": [
                "اقدر أحول من كلية تانية؟", "في تحويل من جامعات؟", "ينفع أحول للكلية؟",
                "ازاي أحول من كلية تانية؟", "التحويل ممكن؟", "اقدر أحول من جامعة تانية؟",
                "في تحويل للكلية؟", "ازاي أنقل من كلية تانية؟"
            ],
            "ما هي لغة التدريس في الكلية؟": [
                "بتدرسوا بأي لغة؟", "اللغة ايه في الدراسة؟", "لغة التدريس ايه؟",
                "الدراسة عربي ولا إنجليزي؟", "ايه لغة الكلية؟", "الكلية بتدرس بأي لغة؟",
                "المواد بتدرس بأي لغة؟", "لغة الدراسة ايه؟"
            ],
            "هل يوجد سكن طلابي؟": [
                "في سكن للطلاب؟", "بتوفروا سكن؟", "في مدينة طلابية؟", "في سكن داخل الكلية؟",
                "السكن متوفر؟", "في أماكن سكن للطلاب؟", "بتديوا سكن للطلاب؟"
            ],
            "هل توفرون كافتيريا؟": [
                "في كافتيريا؟", "بتوفروا كافتيريا؟", "في مكان للأكل؟", "الكلية فيها كافتيريا؟",
                "في مطعم في الكلية؟", "بتقدموا أكل في الكلية؟"
            ],
            "من أنت؟": [
                "انت مين؟", "مين بيكلمني؟", "ايه اسمك؟", "انت ايه؟", "مين ده؟",
                "ايه البوت ده؟", "انت بتعمل ايه؟"
            ],
            "هل أنت بوت؟": [
                "انت بوت؟", "دي آلة بترد؟", "انت روبوت؟", "ايه ده بوت؟", "انت برنامج؟"
            ],
        }

        # معجم لتصحيح الأخطاء الإملائية الشائعة يدويًا
        self.common_corrections = {
            "مددة": "مدة",
            "دراسسة": "دراسة",
            "اقسسام": "أقسام",
            "تخصخصات": "تخصصات",
            "كليية": "كلية",
            "تقدديم": "تقديم",
            "لغغه": "لغة",
            "بكالريوس": "بكالوريوس",
            "دبللوم": "دبلوم",
            "كافتيرا": "كافتيريا",
            "سككن": "سكن"
        }

    def correct_spelling(self, question):
        """
        تصحيح الأخطاء الإملائية باستخدام معجم يدوي ومكتبة ar-corrector.
        """
        for wrong, correct in self.common_corrections.items():
            question = re.sub(r'\b' + wrong + r'\b', correct, question)

        try:
            corrected = self.corrector.spell_correct(question)
            if isinstance(corrected, list):
                corrected = corrected[0][0] if corrected else question
            elif isinstance(corrected, dict):
                corrected = corrected.get('corrected', question)
            logging.info(f"تم تصحيح السؤال: {question} -> {corrected}")
            return corrected
        except (AttributeError, TypeError, IndexError) as e:
            logging.warning(f"فشل تصحيح السؤال '{question}': {str(e)}")
            return question

    def normalize_question(self, question):
        """
        توحيد السؤال بتصحيح الأخطاء الإملائية ومطابقته مع العبارات المعادلة.
        """
        question = re.sub(r'[^\w\s]', '', question).strip()
        question = self.correct_spelling(question)

        for standard_phrase, variations in self.phrases_equivalent.items():
            if question in variations:
                logging.info(f"تم توحيد السؤال: {question} -> {standard_phrase}")
                return standard_phrase

        best_match = None
        best_score = 0
        for standard_phrase, variations in self.phrases_equivalent.items():
            for variation in variations + [standard_phrase]:
                score = fuzz.ratio(question, variation)
                if score > best_score and score > 70:
                    best_score = score
                    best_match = standard_phrase

        if best_match:
            logging.info(f"تم توحيد السؤال باستخدام التشابه: {question} -> {best_match}")
            return best_match
        return question

    def extract_keywords(self, question):
        """
        استخراج الكلمات المفتاحية من السؤال مع استبعاد الكلمات الشائعة.
        """
        stopwords = ['في', 'ايه', 'ازاي', 'هل', 'ما', 'كيف', 'على', 'مع', 'من', 'لو']
        words = re.findall(r'\w+', question)
        return [word for word in words if word not in stopwords]

    def get_response(self, question):
        """
        الحصول على رد بناءً على السؤال بعد توحيده ومطابقته مع الـ intents.
        """
        normalized_question = self.normalize_question(question)

        for intent in self.intents:
            if normalized_question in intent['questions']:
                response = random.choice(intent['responses'])
                logging.info(f"تم العثور على رد للسؤال: {normalized_question} -> {response}")
                return response

        best_match = None
        best_score = 0
        for intent in self.intents:
            for q in intent['questions']:
                score = fuzz.ratio(normalized_question, q)
                if score > best_score and score > 75:
                    best_score = score
                    best_match = random.choice(intent['responses'])

        if best_match:
            logging.info(f"تم العثور على رد باستخدام التشابه: {normalized_question} -> {best_match}")
            return best_match

        keywords = self.extract_keywords(normalized_question)
        for intent in self.intents:
            for q in intent['questions']:
                question_keywords = self.extract_keywords(q)
                if len(set(keywords) & set(question_keywords)) > 1:
                    response = random.choice(intent['responses'])
                    logging.info(f"تم العثور على رد باستخدام الكلمات المفتاحية: {normalized_question} -> {response}")
                    return response

        suggested_questions = [
            "مدة الدراسة كام؟",
            "ايه الأقسام المتاحة؟",
            "ازاي أقدم في الكلية؟"
        ]
        response = (f"عذرًا، لم أستطع فهم سؤالك. جرب صيغة أخرى مثل: "
                    f"{random.choice(suggested_questions)} أو تواصل مع إدارة الكلية عبر الموقع الرسمي.")
        logging.info(f"رد افتراضي للسؤال: {normalized_question}")
        return response

# تهيئة البوت
bot = ChatBot(data_file=str(settings.BASE_DIR / 'chatbot' /
                            'json' / 'intents.json'))

class ChatAPIView(APIView):
    """
    نقطة نهاية API لاستقبال سؤال المستخدم وإرجاع رد البوت.
    """
    def post(self, request):
        question = request.data.get('question')
        if not question:
            return Response({"error": "يرجى إدخال سؤال"}, status=status.HTTP_400_BAD_REQUEST)
        
        response = bot.get_response(question)
        return Response({"response": response}, status=status.HTTP_200_OK)