import requests
from bs4 import BeautifulSoup
import re
import string
import joblib
import tkinter as tk
from tkinter import ttk, messagebox
from langdetect import detect
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# -----------------------------------------------------------
def extract_text_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Kiểm tra nếu có lỗi HTTP
    except requests.RequestException as e:
        return None, f"Lỗi khi tải trang {url}: {e}"
    
    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ' '.join([para.get_text() for para in paragraphs])
        return text, None
    except Exception as e:
        return None, f"Lỗi khi phân tích cú pháp HTML cho {url}: {e}"

# -----------------------------------------------------------
def clean_text(text):
    text = text.lower()
    text = re.sub(f'[{re.escape(string.punctuation)}]', '', text)  # Loại bỏ dấu câu
    text = re.sub(r'\s+', ' ', text)  # Loại bỏ khoảng trắng thừa
    return text.strip()

# -----------------------------------------------------------
def load_model(model_path):
    return joblib.load(model_path)

# -----------------------------------------------------------
def is_fake_news(text, model, vectorizer):
    text_cleaned = clean_text(text)
    text_vectorized = vectorizer.transform([text_cleaned])
    prediction = model.predict(text_vectorized)
    return prediction[0] == 1  # 1: Fake news, 0: Real news

def detect_language(text):
    try:
        language = detect(text)
        return language
    except:
        return "Không xác định"

# -----------------------------------------------------------
def complexity(text):
    words = word_tokenize(text)
    sentences = sent_tokenize(text)
    word_count = len(words)
    sentence_count = len(sentences)
    complexity_score = word_count / sentence_count
    return complexity_score

def extract_subject(text):
    # -----------------------------------------------------------
    subject_keywords = ['Sports', 'Politics', 'Business', 'Education', 'Entertainment', 'Health', 'Science']

    # -----------------------------------------------------------
    max_count = 0
    max_subject = None
    for keyword in subject_keywords:
        count = text.lower().count(keyword)
        if count > max_count:
            max_count = count
            max_subject = keyword

    return max_subject if max_subject else "Không xác định"

# -----------------------------------------------------------
def highlight_fake_parts(text, model, vectorizer):
    fake_parts = []
    sentences = sent_tokenize(text)
    for sentence in sentences:
        if is_fake_news(sentence, model, vectorizer):
            fake_parts.append(sentence)
    
    return '\n'.join(fake_parts)

# -----------------------------------------------------------
def display_checked_text(text, model, vectorizer):
    sentences = sent_tokenize(text)
    for sentence in sentences:
        if is_fake_news(sentence, model, vectorizer):
            text_result_text.insert(tk.END, sentence + '\n', 'fake')
        else:
            text_result_text.insert(tk.END, sentence + '\n')



# -----------------------------------------------------------

# -----------------------------------------------------------
true_news_count = 0
fake_news_count = 0
true_news_urls = []
fake_news_urls = []

# -----------------------------------------------------------
def check_url():
    global true_news_count, fake_news_count
    
    url = url_entry.get()
    if not url:
        return
    
    language = detect_language(url)
    if language == 'en':
        model = load_model('fake_news_detector_en.pkl')
        vectorizer = load_model('tfidf_vectorizer_en.pkl')
    else:
        model = load_model('fake_news_detector_vi.pkl')
        vectorizer = load_model('tfidf_vectorizer_vi.pkl')

    text, error = extract_text_from_url(url)
    if error:
        messagebox.showerror("Lỗi", error)
        return

    if text is None:
        messagebox.showerror("Lỗi", "Không thể trích xuất văn bản từ URL")
        return

    is_fake = is_fake_news(text, model, vectorizer)
    result = "Tin giả" if is_fake else "Tin thật"

    # -----------------------------------------------------------
    language = detect_language(text)
    text_complexity = complexity(text)
    
    # -----------------------------------------------------------
    if is_fake:
        fake_news_count += 1
        fake_news_urls.append(url)
    else:
        true_news_count += 1
        true_news_urls.append(url)
    
    # -----------------------------------------------------------
    total = true_news_count + fake_news_count
    true_news_percent = (true_news_count / total) * 100 if total > 0 else 0
    fake_news_percent = (fake_news_count / total) * 100 if total > 0 else 0
    
    # -----------------------------------------------------------
    result_label.config(text=f"Kết quả: {result}")
    count_label.config(text=f"Tin thật đã phát hiện: {true_news_count} ({true_news_percent:.2f}%), Tin giả đã phát hiện: {fake_news_count} ({fake_news_percent:.2f}%)")
    
    # -----------------------------------------------------------
    text_result_text.delete(1.0, tk.END)
    text_result_text.insert(tk.END, f"URL: {url}\n\nVăn bản: {text}\n\nKết quả: {result}\n\nNgôn ngữ: {language}\n\nĐộ phức tạp: {text_complexity:.2f}")

    # -----------------------------------------------------------
    language_result_label.config(text=f"{language}")
    complexity_result_label.config(text=f"{text_complexity:.2f}")

    # -----------------------------------------------------------
    subject = extract_subject(text)

    # -----------------------------------------------------------
    subject_result_label.config(text=f"{subject}")

    # -----------------------------------------------------------
    fake_parts_text = highlight_fake_parts(text, model, vectorizer)
    fake_text_result_text.delete(1.0, tk.END)
    fake_text_result_text.insert(tk.END, fake_parts_text)

    # -----------------------------------------------------------
    text_result_text.delete(1.0, tk.END)
    display_checked_text(text, model, vectorizer)


# -----------------------------------------------------------
root = tk.Tk()
root.title("Kiểm tra tin tức giả")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

url_label = ttk.Label(frame, text="Nhập URL:")
url_label.grid(row=0, column=0, sticky=tk.W)

url_entry = ttk.Entry(frame, width=50)
url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
url_entry.focus()

check_button = ttk.Button(frame, text="Kiểm tra", command=check_url)
check_button.grid(row=0, column=2, sticky=tk.W)

result_label = ttk.Label(frame, text="")
result_label.grid(row=1, column=0, columnspan=3, sticky=tk.W)

count_label = ttk.Label(frame, text="Tin thật: 0, Tin giả: 0")
count_label.grid(row=2, column=0, columnspan=3, sticky=tk.W)

# -----------------------------------------------------------
text_result_frame = ttk.LabelFrame(frame, text="Văn bản đã kiểm tra", padding="10")
text_result_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E))

text_result_text = tk.Text(text_result_frame, height=10, wrap="word")
text_result_text.pack(fill=tk.BOTH, expand=True)

# -----------------------------------------------------------
text_result_text.tag_config('fake', foreground='red')

# -----------------------------------------------------------
text_percentage_label = ttk.Label(frame, text="")
text_percentage_label.grid(row=4, column=0, columnspan=3, sticky=tk.W)

language_label = ttk.Label(frame, text="Ngôn ngữ:")
language_label.grid(row=4, column=0, sticky=tk.W)

language_result_label = ttk.Label(frame, text="")
language_result_label.grid(row=4, column=1, columnspan=2, sticky=tk.W)

complexity_label = ttk.Label(frame, text="Độ phức tạp:")
complexity_label.grid(row=5, column=0, sticky=tk.W)

complexity_result_label = ttk.Label(frame, text="")
complexity_result_label.grid(row=5, column=1, columnspan=2, sticky=tk.W)

subject_label = ttk.Label(frame, text="Chủ đề:")
subject_label.grid(row=8, column=0, sticky=tk.W)

subject_result_label = ttk.Label(frame, text="")
subject_result_label.grid(row=8, column=1, columnspan=2, sticky=tk.W)

# -----------------------------------------------------------
fake_text_label = ttk.Label(frame, text="Các phần được cho là giả:")
fake_text_label.grid(row=9, column=0, sticky=tk.W)

fake_text_result_text = tk.Text(frame, height=5, wrap="word")
fake_text_result_text.grid(row=9, column=1, columnspan=2, sticky=(tk.W, tk.E))

# -----------------------------------------------------------
check_url()

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
frame.columnconfigure(1, weight=1)

root.mainloop()
