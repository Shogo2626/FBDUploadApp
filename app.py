from flask import Flask, render_template, request, send_file, session
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッションを使うために必要な設定
UPLOAD_FOLDER = "./uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 各種選択肢のデータ
countries = ["中国", "インド", "パキスタン", "バングラデシュ", "インドネシア", "タイ", "ベトナム", "アメリカ", "ウズベキスタン", "韓国", "台湾", "日本"]
adjusters = ["サービス技師", "お客様"]
ics_usages = ["ICS設定値から調整", "既存設定値から調整", "ICS設定値から変更なし", "ICS不使用（手動設定）", "不明"]
running_judgments = ["合格", "不合格", "不明"]
quality_judgments = ["合格", "不合格", "不明"]

category_mapping = {
    "稼動-経停台低減": ["リード揺動範囲", "綜絖枠内", "最終綜絖枠～経糸止装置間", "経糸止装置内", "経糸止装置～ビーム間"],
    "稼動-緯停台低減": [
        "入口くぐり", "入口ループ", "大ループ", "エンドループ", "エンドちぢれ",
        "先端飛びだし", "途中切れ", "捨耳掴まず", "上糸くぐり", "下糸くぐり",
        "ムダ止まり", "ロングピック（長尺）", "ショートピック（短尺）",
        "ドラム～メイン間切れ", "カッターミス", "先端切れ (吹き切れ)", "張り切れ"
    ]
}

change_areas = [
    "バック", "ドロッパ", "イージング", "テンプル", "耳", "緯入れ-メイン系",
    "カッター", "開口角", "開口量", "枠高さ", "ドエル", "クロスタイミング",
    "エア圧力", "タオル", "緯入れ-サブ系", "張力", "Motor設定",
    "MARK設定", "T0-Tw", "Tw-Ctrl", "フィーラ設定", "その他"
]

# ********************************************************************************
# アップロードページ
# ********************************************************************************
@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        uploaded_file = request.files["file"]
        if uploaded_file.filename != "":
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
            uploaded_file.save(file_path)  # ファイルを保存
            session["current_file"] = uploaded_file.filename  # セッションにファイル名を保存
            return render_template(
                "form.html",
                file_name=uploaded_file.filename,
                countries=countries,
                adjusters=adjusters,
                ics_usages=ics_usages,
                running_judgments=running_judgments,
                quality_judgments=quality_judgments
            )
    return render_template("upload.html")

# ********************************************************************************
# 基本情報入力ページの保存処理
# ********************************************************************************
@app.route("/save", methods=["POST"])
def save_data():
    file_name = session.get("current_file")
    if not file_name:
        # セッションにファイル名がない場合エラーを返す
        return "エラー: ファイルが指定されていません", 400

    # HTMLフォームからPOSTデータを取得
    basic_info = {
        "customer": request.form["customer_name"],
        "country": request.form["country"],
        "reporter": request.form["reporter"],
        "adjuster": request.form["adjuster"],
        "ics_usage": request.form["ics_usage"],
        "running": request.form["running"],
        "quality": request.form["quality"]
    }

    # セッションに保存
    session["basic_info"] = basic_info

    # 現象リストを初期化しつつ次の画面へ
    session["phenomena"] = []
    return render_template(
        "phenomenon.html",
        file_name=file_name,
        categories=category_mapping,
        change_areas=change_areas,
        phenomena=session.get("phenomena", [])
    )

# ********************************************************************************
# 現象入力画面
# ********************************************************************************
@app.route("/phenomenon", methods=["GET", "POST"])
def phenomenon_input():
    file_name = session.get("current_file")
    if not file_name:
        return "エラー: ファイルが見つかりません", 400

    if request.method == "POST":
        category = request.form["category"]
        subcategory = request.form["subcategory"]
        change_area = request.form["change_area"]
        phenomena = session.get("phenomena", [])
        phenomena.append((category, subcategory, change_area))
        session["phenomena"] = phenomena

    return render_template(
        "phenomenon.html",
        file_name=file_name,
        categories=category_mapping,
        change_areas=change_areas,
        phenomena=session["phenomena"]
    )

# ********************************************************************************
# 現象データ保存処理
# ********************************************************************************
@app.route("/save_phenomena", methods=["POST"])
def save_phenomena():
    file_name = session.get("current_file")
    if not file_name:
        return "エラー: ファイル名が提供されていません", 400
    
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    if not os.path.exists(file_path):
        return f"エラー: ファイルが見つかりません ({file_path})", 400
    
    basic_info = session.get("basic_info", {})
    phenomenon_data = session.get("phenomena", [])

    # TODO: ファイル処理内容をここに記述
    processed_file_name = f"processed_{file_name}"
    processed_file_path = os.path.join(UPLOAD_FOLDER, processed_file_name)

    # サンプル：処理した結果を新しいファイルとして保存
    with open(processed_file_path, "w", encoding="utf-8") as file:
        file.write("Phenomenon Data Processed\n")  # ダミーデータ

    return send_file(processed_file_path, as_attachment=True)

# ********************************************************************************
# サーバーの起動
# ********************************************************************************
if __name__ == "__main__":
    app.run(debug=True)
