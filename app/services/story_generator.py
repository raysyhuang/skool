"""Graded micro-stories for Chinese reading practice.

Stories are short (3-5 sentences), tagged by difficulty,
and include a comprehension question at the end.
"""

STORIES = [
    {
        "id": 1,
        "title": "The Cat",
        "min_mastery": 0,
        "sentences": [
            {"zh": "\u8FD9\u662F\u4E00\u53EA\u732B\u3002", "pinyin": "zh\u00E8 sh\u00EC y\u012B zh\u012B m\u0101o", "en": "This is a cat."},
            {"zh": "\u732B\u5F88\u5C0F\u3002", "pinyin": "m\u0101o h\u011Bn xi\u01CEo", "en": "The cat is small."},
            {"zh": "\u732B\u559C\u6B22\u5403\u9C7C\u3002", "pinyin": "m\u0101o x\u01D0hu\u0101n ch\u012B y\u00FA", "en": "The cat likes to eat fish."},
        ],
        "question": {
            "text": "What does the cat like to eat?",
            "options": ["Fish", "Rice", "Fruit"],
            "answer": "Fish",
        },
    },
    {
        "id": 2,
        "title": "My Family",
        "min_mastery": 0,
        "sentences": [
            {"zh": "\u6211\u6709\u4E00\u4E2A\u5BB6\u3002", "pinyin": "w\u01D2 y\u01D2u y\u012B g\u00E8 ji\u0101", "en": "I have a family."},
            {"zh": "\u7238\u7238\u5F88\u9AD8\u3002", "pinyin": "b\u00E0ba h\u011Bn g\u0101o", "en": "Dad is tall."},
            {"zh": "\u5988\u5988\u5F88\u7F8E\u3002", "pinyin": "m\u0101ma h\u011Bn m\u011Bi", "en": "Mom is beautiful."},
            {"zh": "\u6211\u5F88\u5F00\u5FC3\u3002", "pinyin": "w\u01D2 h\u011Bn k\u0101ix\u012Bn", "en": "I am very happy."},
        ],
        "question": {
            "text": "How does the child feel?",
            "options": ["Happy", "Sad", "Tired"],
            "answer": "Happy",
        },
    },
    {
        "id": 3,
        "title": "Colors",
        "min_mastery": 0,
        "sentences": [
            {"zh": "\u592A\u9633\u662F\u7EA2\u8272\u7684\u3002", "pinyin": "t\u00E0iy\u00E1ng sh\u00EC h\u00F3ngs\u00E8 de", "en": "The sun is red."},
            {"zh": "\u6811\u662F\u7EFF\u8272\u7684\u3002", "pinyin": "sh\u00F9 sh\u00EC l\u01DCs\u00E8 de", "en": "Trees are green."},
            {"zh": "\u5929\u662F\u84DD\u8272\u7684\u3002", "pinyin": "ti\u0101n sh\u00EC l\u00E1ns\u00E8 de", "en": "The sky is blue."},
        ],
        "question": {
            "text": "What color is the sky?",
            "options": ["Blue", "Red", "Green"],
            "answer": "Blue",
        },
    },
    {
        "id": 4,
        "title": "At School",
        "min_mastery": 1,
        "sentences": [
            {"zh": "\u6211\u53BB\u5B66\u6821\u3002", "pinyin": "w\u01D2 q\u00F9 xu\u00E9xi\u00E0o", "en": "I go to school."},
            {"zh": "\u6211\u559C\u6B22\u8BFB\u4E66\u3002", "pinyin": "w\u01D2 x\u01D0hu\u0101n d\u00FA sh\u016B", "en": "I like to read books."},
            {"zh": "\u8001\u5E08\u5F88\u597D\u3002", "pinyin": "l\u01CEosh\u012B h\u011Bn h\u01CEo", "en": "The teacher is good."},
            {"zh": "\u6211\u6709\u5F88\u591A\u670B\u53CB\u3002", "pinyin": "w\u01D2 y\u01D2u h\u011Bn du\u014D p\u00E9ngy\u01D2u", "en": "I have many friends."},
        ],
        "question": {
            "text": "What does the child like to do?",
            "options": ["Read books", "Play sports", "Sleep"],
            "answer": "Read books",
        },
    },
    {
        "id": 5,
        "title": "Food",
        "min_mastery": 1,
        "sentences": [
            {"zh": "\u6211\u559C\u6B22\u5403\u996D\u3002", "pinyin": "w\u01D2 x\u01D0hu\u0101n ch\u012B f\u00E0n", "en": "I like to eat rice."},
            {"zh": "\u5988\u5988\u505A\u7684\u996D\u5F88\u597D\u5403\u3002", "pinyin": "m\u0101ma zu\u00F2 de f\u00E0n h\u011Bn h\u01CEo ch\u012B", "en": "Mom's cooking is delicious."},
            {"zh": "\u6211\u4E5F\u559C\u6B22\u5403\u9762\u3002", "pinyin": "w\u01D2 y\u011B x\u01D0hu\u0101n ch\u012B mi\u00E0n", "en": "I also like to eat noodles."},
        ],
        "question": {
            "text": "Who cooks delicious food?",
            "options": ["Mom", "Dad", "Teacher"],
            "answer": "Mom",
        },
    },
    {
        "id": 6,
        "title": "The Park",
        "min_mastery": 1,
        "sentences": [
            {"zh": "\u4ECA\u5929\u5929\u6C14\u5F88\u597D\u3002", "pinyin": "j\u012Bnti\u0101n ti\u0101nq\u00EC h\u011Bn h\u01CEo", "en": "Today the weather is nice."},
            {"zh": "\u6211\u4EEC\u53BB\u516C\u56ED\u3002", "pinyin": "w\u01D2men q\u00F9 g\u014Dngyuan", "en": "We go to the park."},
            {"zh": "\u6211\u770B\u5230\u82B1\u548C\u9E1F\u3002", "pinyin": "w\u01D2 k\u00E0n d\u00E0o hu\u0101 h\u00E9 ni\u01CEo", "en": "I see flowers and birds."},
            {"zh": "\u6211\u5F88\u5F00\u5FC3\u3002", "pinyin": "w\u01D2 h\u011Bn k\u0101ix\u012Bn", "en": "I am very happy."},
        ],
        "question": {
            "text": "Where do they go?",
            "options": ["The park", "The school", "The store"],
            "answer": "The park",
        },
    },
    {
        "id": 7,
        "title": "My Dog",
        "min_mastery": 2,
        "sentences": [
            {"zh": "\u6211\u6709\u4E00\u53EA\u72D7\u3002", "pinyin": "w\u01D2 y\u01D2u y\u012B zh\u012B g\u01D2u", "en": "I have a dog."},
            {"zh": "\u5B83\u53EB\u5C0F\u767D\u3002", "pinyin": "t\u0101 ji\u00E0o xi\u01CEo b\u00E1i", "en": "Its name is Xiao Bai."},
            {"zh": "\u5C0F\u767D\u559C\u6B22\u8DD1\u3002", "pinyin": "xi\u01CEo b\u00E1i x\u01D0hu\u0101n p\u01CEo", "en": "Xiao Bai likes to run."},
            {"zh": "\u6211\u548C\u5C0F\u767D\u4E00\u8D77\u73A9\u3002", "pinyin": "w\u01D2 h\u00E9 xi\u01CEo b\u00E1i y\u012Bq\u01D0 w\u00E1n", "en": "I play with Xiao Bai."},
        ],
        "question": {
            "text": "What does Xiao Bai like to do?",
            "options": ["Run", "Sleep", "Eat"],
            "answer": "Run",
        },
    },
    {
        "id": 8,
        "title": "Numbers",
        "min_mastery": 2,
        "sentences": [
            {"zh": "\u4E00\u4E8C\u4E09\u56DB\u4E94\u3002", "pinyin": "y\u012B \u00E8r s\u0101n s\u00EC w\u01D4", "en": "One two three four five."},
            {"zh": "\u4E0A\u5C71\u6253\u8001\u864E\u3002", "pinyin": "sh\u00E0ng sh\u0101n d\u01CE l\u01CEoh\u01D4", "en": "Go up the mountain to find a tiger."},
            {"zh": "\u8001\u864E\u4E0D\u5728\u5BB6\u3002", "pinyin": "l\u01CEoh\u01D4 b\u00FA z\u00E0i ji\u0101", "en": "The tiger is not home."},
            {"zh": "\u53EA\u770B\u5230\u5C0F\u677E\u9F20\u3002", "pinyin": "zh\u01D0 k\u00E0n d\u00E0o xi\u01CEo s\u014Dngsh\u01D4", "en": "Only see a little squirrel."},
        ],
        "question": {
            "text": "What animal did they find?",
            "options": ["Squirrel", "Tiger", "Cat"],
            "answer": "Squirrel",
        },
    },
    {
        "id": 9,
        "title": "Shopping",
        "min_mastery": 3,
        "sentences": [
            {"zh": "\u5988\u5988\u5E26\u6211\u53BB\u8D85\u5E02\u3002", "pinyin": "m\u0101ma d\u00E0i w\u01D2 q\u00F9 ch\u0101osh\u00EC", "en": "Mom takes me to the supermarket."},
            {"zh": "\u6211\u4EEC\u4E70\u4E86\u6C34\u679C\u3002", "pinyin": "w\u01D2men m\u01CEi le shu\u01D0gu\u01D2", "en": "We bought fruit."},
            {"zh": "\u82F9\u679C\u5F88\u7EA2\u3002", "pinyin": "p\u00EDnggu\u01D2 h\u011Bn h\u00F3ng", "en": "The apples are very red."},
            {"zh": "\u6211\u559C\u6B22\u5403\u82F9\u679C\u3002", "pinyin": "w\u01D2 x\u01D0hu\u0101n ch\u012B p\u00EDnggu\u01D2", "en": "I like to eat apples."},
        ],
        "question": {
            "text": "Where did they go?",
            "options": ["Supermarket", "School", "Park"],
            "answer": "Supermarket",
        },
    },
    {
        "id": 10,
        "title": "Bedtime",
        "min_mastery": 3,
        "sentences": [
            {"zh": "\u5929\u9ED1\u4E86\u3002", "pinyin": "ti\u0101n h\u0113i le", "en": "It's dark."},
            {"zh": "\u6708\u4EAE\u51FA\u6765\u4E86\u3002", "pinyin": "yu\u00E8li\u00E0ng ch\u016Bl\u00E1i le", "en": "The moon came out."},
            {"zh": "\u661F\u661F\u4EAE\u4EAE\u7684\u3002", "pinyin": "x\u012Bngx\u012Bng li\u00E0ngli\u00E0ng de", "en": "The stars are bright."},
            {"zh": "\u6211\u8981\u7761\u89C9\u4E86\u3002", "pinyin": "w\u01D2 y\u00E0o shu\u00ECji\u00E0o le", "en": "I'm going to sleep."},
            {"zh": "\u665A\u5B89\uFF01", "pinyin": "w\u01CEn\u0101n", "en": "Good night!"},
        ],
        "question": {
            "text": "What time of day is it?",
            "options": ["Night", "Morning", "Afternoon"],
            "answer": "Night",
        },
    },
]


def get_available_stories(avg_mastery: float = 0) -> list[dict]:
    """Return stories the user can access based on average mastery."""
    result = []
    for story in STORIES:
        result.append({
            **story,
            "unlocked": avg_mastery >= story["min_mastery"],
        })
    return result
