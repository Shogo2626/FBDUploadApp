from flask import Flask, render_template, request, send_file, session
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッションを使うために必要な設定
UPLOAD_FOLDER = "./uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 各種データ設定
countries = ["中国", "インド", "パキスタン", "バングラデシュ", "インドネシア", 
             "タイ", "ベトナム", "アメリカ", "ウズベキスタン", "韓国", "台湾", "日本"]
adjusters = ["サービス技師", "お客様"]
ics_usages = ["ICS設定値から調整", "既存設定値から調整", "ICS設定値から変更なし", 
              "ICS不使用（手動設定）", "不明"]
running_judgments = ["合格", "不合格", "不明"]
quality_judgments = ["合格", "不合格", "不明"]

category_mapping = {
    "稼動-経停台低減": ["リード揺動範囲", "綜絖枠内", "最終綜絖枠～経糸止装置間", 
                      "経糸止装置内", "経糸止装置～ビーム間"]
}

change_areas = ["バック", "ドロッパ", "イージング", "テンプル", "耳", 
                "緯入れ-メイン系", "カッター", "開口角", "開口量", "枠高さ", 
                "ドエル", "クロスタイミング", "エア圧力", "タオル", 
                "緯入れ-サブ系", "張力", "Motor設定", "MARK設定", 
                "T0-Tw", "Tw-Ctrl", "フィーラ設定", "その他"]

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
            session["current_file"] = uploaded_file.filename  # セッション情報に保存
            return render_template(
                "form.html",  # 基本情報入力ページ
                file_name=uploaded_file.filename,
                countries=countries,
                adjusters=adjusters,
                ics_usages=ics_usages,
                running_judgments=running_judgments,
                quality_judgments=quality_judgments
            )
    return render_template("upload.html")  # ファイルアップロードページ

# ********************************************************************************
# 基本情報の保存処理
# ********************************************************************************
@app.route("/save", methods=["POST"])
def save_data():
    file_name = session.get("current_file")
    if not file_name:
        return "エラー: ファイルが指定されていません", 400

    # フォームから取得したデータをセッションに保存
    basic_info = {
        "customer": request.form["customer_name"],
        "country": request.form["country"],
        "reporter": request.form["reporter"],
        "adjuster": request.form["adjuster"],
        "ics_usage": request.form["ics_usage"],
        "running": request.form["running"],
        "quality": request.form["quality"]
    }
    session["basic_info"] = basic_info

    # 現象データ入力画面へ遷移
    session["phenomena"] = []  # 現象データを初期化
    return render_template(
        "phenomenon.html",  # 現象データ入力ページ
        file_name=file_name,
        categories=category_mapping,
        change_areas=change_areas,
        phenomena=session["phenomena"]
    )

# ********************************************************************************
# 現象データの保存と追記
# ********************************************************************************
@app.route("/save_phenomena", methods=["POST"])
def save_phenomena():
    file_name = session.get("current_file")
    if not file_name:
        return "エラー: ファイル名が提供されていません", 400

    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    if not os.path.exists(file_path):
        return f"エラー: ファイルが見つかりません ({file_path})", 400

    # 元のファイル内容を読み込む
    with open(file_path, "r", encoding="utf-8") as file:
        original_content = file.readlines()

    # セッションに保存されている基本情報と現象データを取得
    basic_info = session.get("basic_info", {})
    phenomenon_data = session.get("phenomena", [])

    # 現象データの整形
    phenomenon_lines = ['"JAT910-Phenomenon DATA -----------"\n']
    for category, subcategory, change_area in phenomenon_data:
        phenomenon_lines.append(f'"{subcategory}","1","{change_area}"\n')

    # 基本情報の整形
    basic_info_lines = ['"JAT700-MCARD-DATA file_info -----------"\n']
    basic_info_lines.append(f'"Customer","{basic_info.get("customer", "")}"\n')
    basic_info_lines.append(f'"Country","{basic_info.get("country", "")}"\n')
    basic_info_lines.append(f'"Reporter","{basic_info.get("reporter", "")}"\n')
    basic_info_lines.append(f'"Adjuster","{basic_info.get("adjuster", "")}"\n')
    basic_info_lines.append(f'"ICS Usage","{basic_info.get("ics_usage", "")}"\n')
    basic_info_lines.append(f'"Running","{basic_info.get("running", "")}"\n')
    basic_info_lines.append(f'"Quality","{basic_info.get("quality", "")}"\n')

    # 書き込み処理：元データ + 現象データ + 基本情報
    processed_file_name = f"processed_{file_name}"  # 保存用の新しいファイル名
    processed_file_path = os.path.join(UPLOAD_FOLDER, processed_file_name)
    with open(processed_file_path, "w", encoding="utf-8") as file:
        file.writelines(original_content)  # 元の内容
        file.writelines(phenomenon_lines)  # 現象データを追加
        file.writelines(basic_info_lines)  # 基本情報を追記

    return send_file(processed_file_path, as_attachment=True)  # ダウンロードさせる

# ********************************************************************************
# サーバー起動
# ********************************************************************************
if __name__ == "__main__":
    app.run(debug=True)