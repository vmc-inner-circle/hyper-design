# 영어 UI 직역투를 피하는 법: 글로벌 스타일·현지화 가이드와 번역투 연구 정리

조사일 2026-10-12. 인용은 원문 그대로 옮겼다. 원문에 근거가 없는 해석은 **[추론]**으로 표시했다.
원문 사본: /tmp/uxw-research/dl/ (MS PDF와 txt, Apple HIG JSON, 새국어생활 PDF, Polaris mdx 등)

---

## 0. 한눈에 보기: UI 요소 자리별 종결 형태

| 자리 | 한국어 종결 형태 | 근거 예시(원문) | 출처 | 비고 |
|---|---|---|---|---|
| 메뉴 명령·버튼 | **명사 / 동사 명사형(-기)**. 목적어가 앞, 동작은 끝 | Save→저장, Save as→다른 이름으로 저장, Cut→잘라내기, File New→새로 만들기, Select All→모두 선택, Display pop-up menu→팝업 메뉴 표시, Launch Task Manager→작업 관리자 실행 | MS 5.4.6 | 영어는 "동사 먼저"(Apple, Polaris, Atlassian)지만 한국어는 어순 때문에 동작이 **끝**에 온다 **[추론: 표에서 일관되게 드러나는 패턴]** |
| 체크박스·옵션 | 명사구 + "안 함" 같은 짧은 끝맺음, 대명사 생략 | Do not warn me about this problem again → 이 문제에 대한 경고 메시지 다시 표시 안 함 | MS 4.1.9 | "me" 생략 |
| 대화 상자·마법사 제목 | **명사구**, 마침표 없음 | Completing the New Connection Wizard → 새 연결 마법사 완료 ("Gerund is used in title sentence.") | MS 4.1.12, 한글 맞춤법 문장 부호 1(1) | 제목에는 마침표를 쓰지 않는 것이 원칙(맞춤법) |
| 확인 질문 제목 | 의문형 한 문장. 합니다체는 "~하시겠습니까?", 가벼운 말투는 "~할까요?" | Do you want to continue? → 계속하시겠습니까? / Get the app? → 앱을 받을까요? | MS 2.1.2, 4.1.11 | "계속하기를 원하십니까?"는 오류로 제시 |
| 진행 상태 | "~하는 중…", 문장이면 "~하고 있습니다" | Saving text file… → 텍스트 파일을 저장하는 중… | MS 4.1.12 | |
| 오류 메시지 | **완결된 문장(~니다/~세요) + 마침표**. 영어가 구(phrase)이면 "~오류 발생"처럼 줄여 쓰고 마침표 없이 | Not enough memory. Continue without Undo? → 메모리가 부족합니다. 취소하지 않고 계속하시겠습니까? / Error Accessing URL Address → URL 주소에 액세스하는 동안 오류 발생 | MS 5.4.2 | 표준 구문: Cannot→"~할 수 없습니다", Failed to→"~하지 못했습니다" |
| 설명문·안내문 | 완결된 문장, **-세요**(-십시오 아님), 마침표 | 다음 단원을 참조하십시오 → 다음 단원을 참조하세요. | MS 2.1.2 | 법률 문서(EULA)만 -십시오 |
| 입력 필드 라벨 | 명사(구), 쌍점 없음 | "Share with" (Do) / "Share with:" (Don't) | Material 2 Writing | 영어 원칙. 한국어에서도 같다고 본다 **[추론]** |
| 툴팁·hover·단독 한 문장 | 마침표 생략 가능 | "Avoid using periods on solitary sentences within these UI elements: Labels, Hover text, Bulleted lists, Dialog body text" | Material 2 Writing | 한국어 규범은 명사형 종결문 단독일 때 마침표 생략을 허용(맞춤법 1(1) 붙임 2) |
| AI 미리 정의된 프롬프트 | 반말 요청 "~해 줘", "~해줄래?" | List ideas… → …아이디어를 나열해 줘. | MS 5.3 | 사용자가 AI에게 하는 말이라 화자가 다르다 |

해요체 서비스(토스 등)로 바꿔 쓰면, 설명문·오류는 "~해요/~하세요/~못했어요", 버튼·메뉴·제목은 위와 같은 명사형을 그대로 쓴다. 이 대응은 **[추론]**이다. MS 가이드는 합니다체 기준이며, 해요체 UI를 직접 다룬 글로벌 공식 가이드는 찾지 못했다.

---

## 1. Microsoft Korean Localization Style Guide (가장 직접적인 1차 자료)

출처: https://download.microsoft.com/download/5/b/6/5b62389f-4e3b-4c77-bc18-94efba2fa7bb/kor-kor-StyleGuide.pdf
(learn.microsoft.com/globalization 의 Microsoft language resources에서 연결되는 공식 PDF)

### 1-1. 직역 금지와 다시 쓰기 허용 (2.1, 2.1.1, 2.1.4)
- 규칙: "Because Microsoft voice means a more conversational style, literally translating the source text may produce target text that is not relevant to customers."
- "It's important for translators to modify or re-write translated strings so that they are more appropriate and natural to Korean customers. … re-write just like you are writing the content yourselves. … Sometimes, you may need to remove any unnecessary content."
- "To achieve a fluent translation, word-to-word translation should be avoided. … Strict word-to-word translation would make the tone stiff and unnatural. … The text may be split into different sentences if necessary, simplified. Sometimes you can omit descriptors to make the text snappier."
- 예: Whether you're at work or at play… → (오) "일하거나 놀거나 관계없이 … 휴대할 수 있습니다." → (정) "근무 중이든 여가를 즐기는 중이든 관계없이 언제 어디서나 … 사용할 수 있습니다." / Stay in touch with Windows → (오) "Windows와 연락하세요." → (정) "Windows와 관련된 소식을 전해드립니다."
- 이유(원문): 문장을 하나씩 직역하면 "the contents will not be natural and even ridiculous. And our customers will not come again." 화면에 실제로 나온 모습을 보고 맥락을 봐야 한다("check the source text in the live pages").

### 1-2. 피해야 할 말: '수행·제공·실행' 군더더기, 딱딱한 한자어 (2.1.2)
- 규칙(원문 한국어): "어려운 한자어를 사용하기보다는 쉽게 이해할 수 있는 우리말 표현을 사용해 주십시오. 또한 서술형 명사(작동, 동작, 설치, 제거, 검색, 감사 등)를 수식하는 표현으로 '수행', '실행', '제공' 등은 사용하지 않는 것이 좋습니다."
- 예:
  - Failed to refresh it. → "새로 고침 수행에 실패했습니다." → **"새로 고치지 못했습니다."**
  - Supply a suitable password. → "알맞은 암호를 제공하십시오." → **"알맞은 암호를 입력하세요."**
  - This document provides an overview… → "…개요를 제공합니다." → **"…기능을 간략하게 설명합니다."**
  - Follow these steps to change your password. → "이 절차들을 수행하여 암호를 변경하십시오." → **"암호를 변경하려면 다음 단계를 따르세요."**
  - Do you want to continue? → "계속하기를 원하십니까?" → **"계속하시겠습니까?"**
  - PowerPoint couldn't find ^1. → "^1이(가) 검색되지 않습니다." → **"^1을(를) 찾을 수 없습니다."** (피동 → 능동)
- 이유: "Microsoft voice avoids an unnecessarily formal tone."

### 1-3. "~에 대한" 직역 (Frequent errors, 2.1.2)
- 원문 제목: "These are some frequent errors due to literal and word-to-word translations"
- Set permissions for this app → "이 앱**에 대한** 사용 권한 설정" → **"이 앱의 사용 권한 설정"**
- …extra roaming charges for data… → "데이터**에 대한** 추가 로밍 요금**에 대해** 신경 쓰지 않으려면" → **"추가 데이터 로밍 요금을 내지 않으려면"**
- 이유: 원문은 '직역 때문에 생기는 잦은 오류'라고만 한다. for/about을 "에 대한/에 대해"로 기계적으로 옮기면 생긴다는 점은 아래 김정우 연구('대하다' 과다)와 맞물린다 **[추론]**.

### 1-4. -십시오 대신 -세요 (2.1.2)
- "For Microsoft voice, use—세요 instead of—십시오 as an ending form to properly address the tone and register. This style conveys more natural and conversational user experiences. Please note that you should use—십시오 when localizing EULA or legal contents to express a formal tone."

### 1-5. 품사 바꾸기: 수식어를 동사·부사로 (4.1.7)
- "In Korean localized text, you often need to translate modifiers into different part of speeches, for example, modifiers can be translated as a meaning of verb, subjective complement, adverb, and etc, for better readability."
- Invalid value for the certificate validator type. → "…형식에 대한 잘못된 값입니다." → **"…형식의 값이 잘못되었습니다."**
- For more effective troubleshooting, use this error message. → "보다 효율적인 문제 해결을 위해서…사용하십시오." → **"보다 효율적으로 문제를 해결하려면 이 오류 메시지를 사용하세요."**
- 이유(원문 Comment): 영어 명사구의 실제 뜻("The value … is invalid", "to troubleshoot more effectively")을 풀어 쓰는 쪽이 "more fluent translation".

### 1-6. 대명사는 대개 생략 (4.1.9)
- "In Korean, pronouns are seldom used in localized text since they decrease readability. The translations of pronouns are often omitted if the meaning of source text can be clearly delivered without translating them. Sometimes pronouns should be translated specifically to clarify what they mean based on the context."
- The object has changed. Do you want to update it? → "개체가 변경되었습니다. 업데이트하시겠습니까?" ("it" 생략)
- Verify your entry and try again. → "입력 내용을 확인하고 다시 시도하세요." ("your" 생략)
- Send a new Welcome Kit based on my new Media selection. → "선택한 미디어에 따라 웰컴 키트를 보내 주세요." ("my" 생략)
- 반례(뜻이 흐려지면 살림): Only allow my team members to see my email addresses → "내 팀 멤버만 내 전자 메일 주소를 볼 수 있도록 허용"
- 사용자 사례 적용: "내 순번은 5번"(My position is 5)의 "내"는 생략 대상이다 **[추론]**.

### 1-7. 소유 중심 → 존재 중심, 짧은 조각문 (4.1.11)
- 원문(한국어): "간단하면서 문법적으로 올바른 표현을 사용하십시오. 가능한 경우, 소유 중심의 영어식 표현은 존재 중심의 우리말 표현으로 바꿔 주십시오."
- You may not have appropriate rights. → "필요한 사용 권한을 가지고 있지 않을 수 있습니다." → **"필요한 권한이 없을 수 있습니다."**
- Here's how. → "다음을 실행하려면 이 방법을 사용하십시오." → **"방법" 또는 "다음과 같이 하세요."**
- This isn't used when running on Microsoft Office 365… → "…이 기능이 활성화되지 않습니다." → **"Microsoft Office 365에서는 이 기능을 사용할 수 없습니다."**
- 동사 have→is 바꾸기 (4.1.12): The engine input file has the wrong version. → **"엔진 입력 파일의 버전이 잘못되었습니다."** ("Rephrase 'has' with 'is'")

### 1-8. 시제와 진행형 (4.1.12)
- "Continuous operations are usually expressed in English with a gerund, which should be translated into Korean as a form of '~ 하고 있습니다' or '~ 하는 중.' A gerund is often used in title sentence in English so it is important to distinguish…"
- Saving text file… → "텍스트 파일을 저장하는 중…" / Completing the New Connection Wizard(제목) → "새 연결 마법사 완료"
- "use simple present as the basic tense unless you are required to use other tenses in the context."

### 1-9. 오류 메시지 (5.4.2)
- "English error messages tend to be shorter and sometimes 'be' verb is omitted, but in Korean, fully developed form of translation is preferred."
- "Error message is generally translated into '~니다' style, in which case, a period should be placed at the end … However, if English text is not a full sentence but a phrase … you can translate them accordingly."
- 표준 구문: Cannot/Could not … → "~할 수 없습니다"("It is not necessary to translate 'could not' into past tense.") / Failed to … → "~하지 못했습니다" / An error occurred while … → "~하는 동안 오류가 발생했습니다"("instead of '~하는 중'")
- 자리표시자 뒤 조사: "double placeholders should be used, for example, 은(는), 이(가), 을(를)…" 숫자 뒤 단위: "%d개의 문서", "%d일 후에는"
- 이유: "translators are encouraged to apply them to ensure target translation is more natural, empathetic and not robot-like."

### 1-10. 영어 줄표(em dash)를 한국어로 옮긴 예 (2.1.1, 2.2.1, 2.2.3)
- 가이드에 줄표를 옮기는 규칙은 따로 없다. 다만 실제 예시를 보면 줄표가 모두 사라진다.
  - "The desktop that you're used to—with its taskbar, folders, and icons—is still here…" → "작업 표시줄, 폴더, 아이콘 등 이전에 사용하던 데스크톱 환경을 그대로 계승하고…" (줄표 삽입구를 앞으로 옮겨 관형절로)
  - "Give your PC a name—any name you want." → "PC에 사용할 이름을 지어 주세요." ("any name you want"는 생략)
  - "You choose the picture—and the gestures you use with it—to create a password…" → "원하는 사진을 선택하고 그 위에 고유한 제스처를 이용하여 사진 암호를 만들 수 있습니다." (줄표를 연결어미 "-고"로)
- 이유: 원문에 설명은 없다. 아래 한글 맞춤법 줄표 조항과 함께 보면 '두 문장을 줄표로 잇는' 쓰임은 한국어 규범에 없다 **[추론]**.

### 1-11. MS 가이드에서 못 찾은 것
- 버튼·메뉴·제목에 각각 어떤 종결을 쓰는지 정리한 표나 규칙은 없다. 위 0번 표는 단축키 표(5.4.6), 대명사 예(4.1.9), 동명사 제목 예(4.1.12), 오류 메시지 예(5.4.2)에서 패턴을 뽑은 것이다.
- "~할 수 있습니다"를 줄이라는 명시 규칙은 없다. 기능 소개 예시에서는 오히려 자주 쓴다(2.1.4, 2.2.3).

---

## 2. Apple

### 2-1. Apple Style Guide
- 출처: https://support.apple.com/guide/applestyleguide/welcome/web
- 미국 영어 기준이며, 현지화 콘텐츠는 각 언어·지역 자료를 보라고 한다(검색 결과 요약 기준). **Apple의 공개 한국어 스타일 가이드는 찾지 못했다.** Apple이 공개하는 것은 OS 번역 문자열 용어집(Glossaries, 개발자 로그인 필요)뿐이다: https://developer.apple.com/localization/resources

### 2-2. Apple HIG – Writing
- 출처: https://developer.apple.com/design/human-interface-guidelines/writing (JSON: /tutorials/data/design/human-interface-guidelines/writing.json)
- 버튼: "When labeling buttons and links, it's almost always best to use a verb. … just saying 'Send' often works better than 'Let's do it!'"
- 소유 대명사 (2025-12-16 추가): "Use possessive pronouns sparingly. Possessive pronouns like my and your are often unnecessary to establish context. For example, 'Favorites' conveys the same message as 'Your Favorites,' and is more succinct. … Avoid using we altogether because it may be unclear who the 'we' in question refers to. … 'We're having trouble loading this content.' Something like 'Unable to load content' is much clearer."
- 흐름 라벨: "Begin with language like 'Get Started' … use terms like 'Continue' or 'Next,' but be consistent … Make it clear when a flow is complete by using language like 'Done.'"
- 오류: "'That password is too short' isn't as helpful as 'Choose a password with at least 8 characters.' … Interjections like 'oops!' … can sound insincere." / "'Use only letters for your name' is better than 'Don't use numbers or symbols.' Avoid robotic error messages … like 'Invalid name.'"
- 설정 라벨: "Describe what it does when turned on, and people can infer the opposite."
- 한국어 대응: "내 순번", "내 예약" 같은 "내"는 영어에서도 줄이라는 쪽이다. 직역해서 생긴 "내"는 지운다 **[추론]**.

### 2-3. Apple HIG – Alerts
- 출처: https://developer.apple.com/design/human-interface-guidelines/alerts
- 제목: "Write a title that clearly and succinctly describes the situation. … Avoid writing a title that doesn't convey useful information — like 'Error' … If the title is a complete sentence, use sentence-style capitalization and appropriate ending punctuation. If the title is a sentence fragment, use title-style capitalization, and don't add ending punctuation."
- 버튼: "Aim for a one- or two-word title that describes the result of selecting the button. Prefer verbs and verb phrases that relate directly to the alert text — for example, 'View All,' 'Reply,' or 'Ignore.' … avoiding 'Yes' and 'No.' Always use 'Cancel' to title a button that cancels the alert's action."
- 한국어 대응: "예/아니요" 대신 "삭제/취소"처럼 결과를 말하는 1~2단어 명사형을 쓴다 **[추론, MS 단축키 표와 같은 형태]**.

### 2-4. Apple HIG – Buttons
- 출처: https://developer.apple.com/design/human-interface-guidelines/buttons
- "consider starting the label with a verb … 'Add to Cart.'" / 진행 중 라벨: "'Checkout' could change to 'Checking out…'"

---

## 3. Google

### 3-1. Material Design 2 – Writing
- 출처: https://m2.material.io/design/communication/writing.html (JS 렌더링 페이지라 r.jina.ai로 본문을 받음)
- 짧게: "Save changes?" (Do) / "Would you like to save your changes?" (Don't)
- 해야 할 일을 말하기: "Register to vote" (Do) / "You must register before you can vote" (Don't): "Tell the user how to take action, not that they should or must do so."
  - 한국어 대응: "~해야 투표할 수 있어요" 대신 "투표 등록". '~할 수 있다'·'~해야 한다'는 영어에서도 줄이는 쪽이다 **[추론]**.
- 인칭: "Address users in either the second person (you or your) or the first person (I, me, or my)… avoid using 'me' or 'my,' and 'you' or 'your,' in the same phrase."
- 시제: "Message sent" (Do) / "Message has been sent" (Don't). 현재형, 단순한 동사 형태.
- 마침표: "Avoid using periods on solitary sentences within these UI elements: Labels, Hover text, Bulleted lists, Dialog body text. Use periods on: Multiple sentences…"
- 쌍점: "Skip colons after labels." "Share with" (Do) / "Share with:" (Don't)
- 쉬운 말: "Turn on Location History" (Do) / "Enable Location History" (Don't)

### 3-2. Material Design 3 – UX writing best practices
- 출처: https://m3.material.io/foundations/content-design/style-guide/ux-writing-best-practices
- "use specific titles and headings that clearly describe a topic." / "All text, including titles, headings, labels, menu items, navigation components, app bars, and buttons should use sentence-style capitalization."
- 결과 설명: "Tell users what will happen if they take an action and how they can undo it"

### 3-3. Android – Localize your app
- 출처: https://developer.android.com/guide/topics/resources/localization
- "make sure to describe the context in which the string is used. … Where is this in the UI? For example, translations are less flexible in buttons than in text boxes."
- 이유: 번역자는 문자열을 화면 맥락 없이 받는다. 같은 영어라도 제목인지 버튼인지에 따라 한국어 꼴이 달라진다(MS 4.1.12 동명사 예와 같은 이유).

### 3-4. Google developer documentation style guide – Write for a global audience
- 출처: https://developers.google.com/style/translation
- "Write shorter sentences." / "don't use more than two nouns as modifiers of another noun." / "Use active voice." / "Clarify antecedents… if a pronoun is ambiguous, then replace it with the appropriate noun." / "Use the conditional clause first." / "Avoid colloquialisms, idioms, or slang." / "Avoid humor."
- **한국어 관련 부분은 없다.** 영어 원문을 쓰는 쪽의 지침이다.
- **Google의 한국어 스타일 가이드는 공개된 것을 찾지 못했다.**

---

## 4. 영어권 디자인 시스템 (한국어와 비교용)

### 4-1. Shopify Polaris
- 출처(공식 저장소, 사이트 폐쇄 뒤 GitHub에 원문이 남아 있음):
  - https://github.com/Shopify/polaris/blob/main/polaris.shopify.com/content/content/fundamentals.mdx
  - https://github.com/Shopify/polaris/blob/main/polaris.shopify.com/content/components/deprecated/modal.mdx
  - https://github.com/Shopify/polaris/blob/main/polaris.shopify.com/content/components/actions/button.mdx
- **"Be direct ('add apps' not 'you can add apps')"**, "Start sentences with verbs so they feel like actionable instructions" (fundamentals)
- 모달 본문: "Actionable: start sentences with imperative verbs when telling a merchant what actions are available to them … Don't use permissive language like 'you can'." Do: "Notification emails will be sent to this address." / "This can't be undone." Don't: "You can edit the email address where emails will be sent."
- 모달 제목: "Use a clear {verb}+{noun} question or statement". Do: "Edit email address", "Delete customer?", "Discard unsaved changes?" Don't: "Are you sure you want to delete customer?", "Discard?"
- 버튼: "Lead with a strong, actionable verb." "Sentence case / No articles / No punctuation". "{verb}+{noun} format on actions except in the case of common actions like Save, Close, Cancel, or OK."
- "Skip the punctuation (exceptions: questions or text with 2+ sentences)"
- 한국어 대응: "you can" 금지는 한국어의 "~할 수 있어요" 남발과 정확히 같은 문제다. 한국어에서 {verb}+{noun}은 어순이 뒤집혀 {명사}+{동작명사}("이메일 주소 수정", "고객 삭제")가 된다 **[추론, MS 단축키 표 패턴과 일치]**.

### 4-2. Atlassian Design System – Button
- 출처: https://atlassian.design/components/button/usage
- "Use action verbs or phrases to tell the user what will happen next" / "Use sentence-case capitalization." / "Keep labels short and free of punctuation. Drop unnecessary articles" / "Start with the verb and specify what is being acted on." / "Don't use vague and generic labels" (Yes/No 대신 Delete) / "if a button is part of a larger modal, use the same language in the button as in headings and other related text."

### 4-3. Mailchimp Content Style Guide
- Web elements: https://styleguide.mailchimp.com/web-elements/
  - "Button copy should always include verbs." "Headings and subheadings are written in sentence case. Avoid using end punctuation except for question marks…" "Titles … Don't use end punctuation in a title unless the title is a question."
- Writing for Translation: https://styleguide.mailchimp.com/writing-for-translation/
  - "Use active voice." "Use the subject-verb-object sentence structure." "Mailchimp's voice is conversational and informal. However, in some cultures, informal text may be considered offensive. Check with your translator…"
  - 모호한 단어: "'Once' (could mean 'one time,' 'after,' 'in the past,' or 'when')", "'Has' or 'have' plus past participle (could confuse the relationship between subject and object)". 영어 원문 단계의 지침이다.

### 4-4. 영어 원칙이 한국어에서 달라지는 점 [모두 추론, 근거는 각 항목 참조]
| 영어 원칙 | 한국어에서는 |
|---|---|
| 버튼은 동사로 시작 (Apple, Polaris, Atlassian) | 동작이 끝에 온다. "고객 삭제", "다른 이름으로 저장"(MS 5.4.6) |
| Sentence case / Title case | 해당 없음. 대신 종결 형태(명사형 / -요 / -다)를 자리별로 통일 |
| 제목에 마침표 없음, 질문은 ? (Mailchimp, Polaris) | 한글 맞춤법도 "제목이나 표어에는 쓰지 않음을 원칙으로 한다" |
| you/your/my 최소화 (Apple) | 한국어는 더 강하게 생략(MS 4.1.9). "당신"은 거의 쓰지 않는다 |
| "you can" 금지 (Polaris) | "~할 수 있어요" 남발 금지. 번역문에 can 구문이 간섭한다는 말뭉치 근거가 있다(5-3) |
| 줄표로 삽입·부연 | 맞춤법상 줄표는 부제, 그리고 쉼표 대신 끼워 넣는 삽입구에만 쓴다(5-4) |
| 조건절 먼저 (Google) | 한국어도 조건이 앞이지만, 조건절만 제목으로 떼어 쓰지 않는다(원문 근거 없음) |

---

## 5. 한국어 번역투 연구 (국립국어원 『새국어생활』 제22권 제1호, 2012 봄 특집 "번역과 국어")

### 5-1. 김순영, 「영한 번역에 나타난 번역투 문장」
- 출처: https://www.korean.go.kr/nkview/nklife/2012_1/22_0105.pdf
- 정의(김정우 2007 인용): "번역투는 어떤 글에 원본이 아닌 번역이라는 흔적이 일정하게 반복적으로 출현하는 텍스트상의 특성"
- **have → 가지다**: "She has a sweet voice. 직역: 그녀는 아름다운 목소리를 가지고 있다. 대안 번역: 그녀는 목소리가 아름답다."(이근희 2005) / "사랑하는 처자를 가진 가장 → 사랑하는 처자가 있는 가장"
- **수동태**: "그 강도는 용감한 시민에 의하여 붙잡혔다 → …시민한테(에게) 붙잡혔다." "…엄청난 노력이 기울여졌다 → …엄청난 노력을 기울였다." 이유: "국어는 영어와 달리 자동사와 타동사의 구별이 엄격하지 않을 뿐더러, 타동사 다음에 반드시 목적어를 쓰지 않아도 된다. … 영어의 문법 구조를 그대로 옮겨 놓을 경우 어색한 우리말이 된다."
- **복수 '-들'**: "아이디어들과 방법들 → 여러 가지 남다른 생각과 방법". 이유: "국어에서는 복수 표시가 꼭 접미어를 통해서만 나타나는 것이 아니다."
- **전치사구**: "'~에 관하여', '~로부터', '~에 의해' 등과 같은 표현들이 이제는 익숙하게 느껴질 만큼 영어의 전치사구는 우리말 문장에 많은 영향을 끼쳤다." 예: "이번 기회를 통해 → 이번 기회에"(through), "폭격에 의해 → 폭격으로"(by), "긴장으로부터의 해방 → 긴장에서 벗어나는"(from)

### 5-2. 강주헌, 「국어다운 번역을 위하여」
- 출처: https://www.korean.go.kr/nkview/nklife/2012_1/22_0108.pdf
- **무생물 주어**: "우리말에서 '허락하다'의 주어로는 사람만 가능하지만 … permit는 사물도 주어로 쓰일 수 있기 때문에 … (현금 인출기는 당신에게 어느 때나 돈을 인출하는 걸 허락한다. → 현금 인출기 덕분에 우리는 돈을 어느 때나 인출할 수 있다.)"
- **'-의' 남용**: "국립국어원 누리집의 '우리말 바로 쓰기'에서도 '-의'를 남용하는 것은 일본어의 영향으로 볼 수 있다며, '효과적인 읽기의 방법을 이야기해 보자.'와 같이 쓰기보다는 '효과적으로 읽는 방법을 이야기해 보자.'와 같이 쓰는 것이 우리말에서 더 자연스럽다고 말한다." 방법: "'-의'로 구성된 명사구에서 중심인 명사를 동사로 풀어쓰면 우리말답게 변하고 이해하기도 쉽다." 예: "에너지 손실의 양 → 에너지가 손실된 양 / 에너지 손실량"
- **조사 겹쓰기**: "~에서의", "~와의", "~로부터": "부모의 종교로부터 벗어나고 → 에서". 이유: "같은 뜻이라면 조사 둘을 결합해 전달하는 것보다 하나의 조사로 전달하는 편이 낫다. 언중이 입말에서 사용하는 단어를 적극적으로 활용하는 번역이 돼야 한다."
- **'-에 있어서'**: "종교 문제에 있어서도 → 종교 문제에서도"
- 결론: "영어에서 명사로 쓰였다고 우리말 번역에서 명사로 번역할 이유는 없다." "그 화합 가능성은 입말에 가까울수록 좋다."

### 5-3. 김정우, 「현대 국어 번역문의 실태」 (김혜영 2009, 100만 어절 비교 말뭉치 연구 소개)
- 출처: https://www.korean.go.kr/nkview/nklife/2012_1/22_0104.pdf
- 영한 번역문에서 비번역문보다 많이 나오는 것(말뭉치 근거):
  - "2인칭 대명사에서는 '당신, 그대, 여러분' 등", "3인칭 대명사에서는 '그, 이것/이거, 그것/그거'"
  - "'만들다, 가지다, 의하다, 대하다' 등의 동사", "통사적 피동에 사용되는 '-아/어 지다'"
  - "관형격 조사 '-의'와 부사격 조사 '-에게서, -으로부터, -으로'", "주격 조사 '-이/가'에 비해 주제 표시 보조사 '-은/는'이 과도하게"
  - "'-수 없다'로 표현되는 어휘적 능력 부정 형식이 많이 나타난다"
  - 상투적 접속어 "'왜냐하면', '만약, 만일', '불구하고'"
- 원인 해석(원문): "'당신, 그대, 여러분' 등과 … '그, 이것/이거, 그것/그거' 등이 많이 쓰인다는 것은 주어를 필수적으로 요구하는 영어 구문을 번역하면서 발생한 현상", "'수 없다' 형식의 빈출 역시 영어 원문의 조동사(can) 구문이 간섭한 결과로 해석할 수 있다."
- 사용자 사례 적용:
  - "내 순번**은** 5번"은 have/be 구문을 직역하고 '-은/는'을 과하게 쓴 경우다 **[추론]**. → "대기 5번째" / "앞에 4명 있어요".
  - "~할 수 있어요" 남발은 can 간섭이다. 말뭉치는 부정형 '수 없다'를 보여 주는데, 긍정형도 같은 기제라고 본다 **[추론]**.

### 5-4. 한글 맞춤법 문장 부호 (문화체육관광부 고시 2014-0039, 2015.1.1 시행)
- 출처: https://korean.go.kr/kornorms/regltn/regltnView.do?regltn_code=0001&regltn_no=1
- **줄표**: "15. 줄표(―) 제목 다음에 표시하는 부제의 앞뒤에 쓴다. … 다만, 뒤에 오는 줄표는 생략할 수 있다." 쉼표 항 (13) 붙임 1: 문장 중간에 끼어든 어구의 앞뒤에 "쉼표 대신 줄표를 쓸 수 있다." 예: "나는 ― 솔직히 말하면 ― 그 말이 별로 탐탁지 않아."
  - 이유: 규정이 정한 줄표 쓰임은 부제와 끼어든 어구 두 가지뿐이다. **영어처럼 두 문장(절)을 줄표 하나로 잇는 쓰임은 규정에 없다.** 그런 문장은 연결어미(-고, -는데, -니까)로 잇거나 두 문장으로 나눈다 **[추론]**. MS 예시(1-10)도 그렇게 처리했다.
- **마침표**: "다만, 제목이나 표어에는 쓰지 않음을 원칙으로 한다." / "용언의 명사형이나 명사로 끝나는 문장에는 쓰는 것을 원칙으로 하되, 쓰지 않는 것을 허용한다." 해설: 명사형 문장이 "단독으로 있을 때는 마침표를 쓰지 않을 수도 있다."

### 5-5. 못 찾은 것 / 확인 못 한 것
- 국립국어원이 "~에 대해", "~를 통해"를 번역투로 판정한 1차 문서(온라인가나다 답변 등)는 찾지 못했다. 위 5-1(through→기회에, 전치사구)와 5-3('대하다' 과다)이 가장 가까운 근거다.
- 『번역의 탄생』(이희재, 2009), 『우리글 바로쓰기』(이오덕) 등 단행본은 본문을 열람하지 못했다. 김순영·강주헌의 인용을 거친 2차 인용만 있다.
- "~할 수 있다"(긍정형) 남용을 직접 다룬 연구 원문은 찾지 못했다. 근거는 5-3의 '-수 없다' 말뭉치 결과와 Polaris "you can" 금지 규칙이다.

---

## 6. 참고: 국내 기업 (요청 범위 밖, 짧게)
- 토스 8가지 라이팅 원칙: https://toss.tech/article/8-writing-principles-of-toss
  - "Weed cutting: 의미 없는 단어를 모두 제거했는가?", "Remove empty sentences", "Easy to speak: 이해하기 어려운 용어나 표현을 사용하지 않았는가?", "Predictable hint: 다음 화면을 예상할 수 있는 힌트가 있는가?"
  - 해요체 통일과 능동형 같은 세부 규칙은 본문 이미지에만 있어 확인하지 못했다. "송금이 완료되었습니다 → OOO님에게 50,000원을 보냈어요" 비교는 제3자 기사(https://yozm.wishket.com/magazine/detail/2000)에서 인용한 것이다.

---

## 7. 사용자 사례에 적용한 규칙 초안 [근거 표시, 결합·적용은 추론]

| 증상 | 규칙 | 고친 예 | 근거 |
|---|---|---|---|
| 섹션 제목 "자리가 나면"(If a spot opens) | 제목은 다루는 대상을 **명사구**로 쓴다. 조건절·연결어미("-면", "-하면")로 끝내지 않는다 | "빈자리 알림" / 본문: "자리가 나면 바로 알려 드려요" | MS 4.1.12(제목 동명사 → "…완료"), M3 "titles … clearly describe a topic", 맞춤법(제목 마침표 없음) |
| "취소하면"(If you cancel) | 위와 같다. 결과는 본문 문장으로 쓴다 | 제목 "취소 안내" / 본문 "취소하면 대기 순번이 사라져요" | 위와 같음, M3 "Tell users what will happen" |
| "내 순번은 5번"(My position is 5) | my/your를 생략하고, be/have 구문을 존재·상태로 바꾼다 | "대기 5번째" / "앞에 4명 있어요" | MS 4.1.9, 4.1.11, Apple "Use possessive pronouns sparingly", 김순영(have→가지다) |
| 두 문장을 줄표(—)로 잇기 | 줄표는 부제와 삽입구에만 쓴다. 절은 연결어미로 잇거나 문장을 나눈다 | "자리가 나면 알려 드려요 — 10분 안에 확정하세요" → "자리가 나면 알려 드려요. 10분 안에 확정해 주세요." | 한글 맞춤법 15, (13) 붙임, MS 1-10 예 |
| "~할 수 있어요" 남발 | 할 수 있음 자체가 정보일 때만 쓴다. 나머지는 동작이나 결과를 바로 말한다 | "여기서 예약을 변경할 수 있어요" → "예약 변경은 여기서 해요" 또는 버튼 "예약 변경" | Polaris "add apps not you can add apps", 김정우 '-수 없다'(can 간섭), M2 "Tell the user how to take action" |
| "~에 대한/~을 통해/~로부터/~의" | 조사 하나로 줄이거나 동사로 풀어 쓴다 | "이 앱에 대한 권한 설정 → 이 앱의 권한 설정", "알림을 통해 확인 → 알림으로 확인" | MS Frequent errors, 김순영 3.3, 강주헌 |
| "~이 수행/제공됩니다", "~되었습니다" 피동 | 서술형 명사 + 수행·제공을 빼고 능동으로 쓴다 | "새로 고침 수행에 실패했습니다 → 새로 고치지 못했습니다" | MS 2.1.2, 김순영 3.1 |
| "당신/그것/이것" | 생략한다. 뜻이 흐려지면 명사를 되풀이한다 | "그것을 업데이트할까요? → 업데이트할까요?" | MS 4.1.9, 김정우 말뭉치 |
| 버튼 "예/아니요", "확인" | 결과를 말하는 1~2단어 명사형 | "삭제" / "취소" | Apple Alerts, Atlassian, MS 5.4.6 |
