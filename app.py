from flask import Flask, render_template, request, redirect, session
import os

# Flaskアプリケーションの初期化
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ファイルアップロードの保存先ディレクトリの設定
UPLOAD_FOLDER = "./uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 各種プルダウンリストの選択肢データ
countries = [
    "中国", "インド", "パキスタン", "バングラデシュ", "インドネシア",
    "タイ", "ベトナム", "アメリカ", "ウズベキスタン", "韓国", "台湾", "日本"
]

adjusters = ["サービス技師", "お客様"]
ics_usages = [
    "ICS設定値から調整", "既存設定値から調整", "ICS設定値から変更なし",
    "ICS不使用（手動設定）", "不明"
]
running_judgments = ["合格", "不合格", "不明"]
quality_judgments = ["合格", "不合格", "不明"]

category_mapping = {
    "稼動-経停台低減": [
        "リード揺動範囲", "綜絖枠内", "最終綜絖枠～経糸止装置間",
        "経糸止装置内", "経糸止装置～ビーム間"
    ],
    "稼動-緯停台低減": [
        "入口くぐり", "入口ループ", "大ループ", "エンドループ", "エンドちぢれ",
        "先端飛びだし", "途中切れ", "捨耳掴まず", "上糸くぐり", "下糸くぐり",
        "ムダ止まり", "ロングピック（長尺）", "ショートピック（短尺）",
        "ドラム～メイン間切れ", "カッターミス"
    ], 
    "品質-経方向": [
        "経糸緩み", "エアーマーク", "サブノズルマーク", "経筋", "布破れ", "地合い不良"
    ],
    "品質-緯方向": [
        "緯糸緩み(左側)", "緯糸緩み(右側)", "筬打ち切れ", "テンプル切れ",
        "フィラメント切れ", "繊維割れ", "ビリ", "左右色差"
    ],
    "品質-耳欠点": [
        "耳吊り", "耳緩み", "耳フレア"
    ],
    "品質-止段": [
        "前厚段-全幅", "後厚段-全幅", "前薄段-全幅", "後薄段-全幅",
        "前厚段-テンプル", "後厚段-テンプル", "前薄段-テンプル", "後薄段-テンプル",
        "前枕段", "後枕段", "ループ段"
    ]
}

change_areas = [
    "バック", "ドロッパ", "イージング", "テンプル", "耳", "緯入れ-メイン系",
    "カッター", "開口角", "開口量", "枠高さ", "ドエル", "クロスタイミング",
    "エア圧力", "タオル", "緯入れ-サブ系", "張力", "Motor設定", "MARK設定",
    "T0-Tw", "Tw-Ctrl", "フィーラ設定", "その他"
]


# *****************************
# アップロード画面
# *****************************
@app.route("/", methods=["GET", "POST"])
def upload_file():
    """ファイルアップロード画面の処理"""
    if request.method == "POST":
        uploaded_file = request.files["file"]
        if uploaded_file.filename:
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
            uploaded_file.save(file_path)  # ファイルを保存
            session["current_file"] = uploaded_file.filename
            return redirect("/phenomenon")  # アップロード後、現象入力画面にリダイレクト
    return render_template("upload.html")


# *****************************
# 現象入力画面
# *****************************
@app.route("/phenomenon", methods=["GET", "POST"])
def phenomenon():
    """現象入力画面の処理"""
    if request.method == "POST":
        # フォームからデータを取得
        category = request.form["category"]
        subcategory = request.form["subcategory"]
        change_area = request.form["change_area"]
        
        # セッションに格納された現象データを取得または初期化
        phenomena = session.get("phenomena", [])
        phenomena.append((category, subcategory, change_area))
        session["phenomena"] = phenomena  # 現象データを更新して格納
    
    return render_template(
        "phenomenon.html",
        file_name=session.get("current_file"),
        categories=categories,
        change_areas=change_areas,
        phenomena=session.get("phenomena", []),
        enumerate=enumerate  # enumerate関数を渡す
    )


# *****************************
# 現象データの削除処理
# *****************************
@app.route("/delete_phenomenon", methods=["POST"])
def delete_phenomenon():
    """特定の現象データを削除する処理"""
    try:
        # 削除対象のデータのインデックスを受け取る
        index = int(request.form["data_index"])
        
        # セッションの現象データリストからインデックスを指定して削除
        phenomena = session.get("phenomena", [])
        if 0 <= index < len(phenomena):  # インデックスが範囲内であることを確認
            phenomena.pop(index)  # データをリストから削除
            session["phenomena"] = phenomena  # 更新結果をセッションに保存
        
        return redirect("/phenomenon")  # 現象入力画面にリダイレクト
    except Exception as e:
        return f"サーバーエラー: {str(e)}", 500


# *****************************
# 現象データの保存処理
# *****************************
@app.route("/save_phenomena", methods=["POST"])
def save_phenomena():
    """すべての現象データを保存する処理"""
    try:
        # ファイル名を取得
        file_name = session.get("current_file")
        if not file_name:
            raise Exception("ファイル名がセッションに存在しません")

        # ファイルパスを確認し、存在しない場合はエラーを送出
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        if not os.path.exists(file_path):
            raise Exception(f"元のファイルが存在しません: {file_path}")

        phenomena = session.get("phenomena", [])  # 現象データを取得
        processed_file_path = os.path.join(UPLOAD_FOLDER, f"processed_{file_name}")
        
        # データを保存するファイルを開く
        with open(processed_file_path, "w", encoding="utf-8") as processed_file:
            for category, subcategory, change_area in phenomena:
                processed_file.write(f"{category},{subcategory},{change_area}\n")
        
        # ファイル保存完了のメッセージ
        return f"現象データを保存しました: {processed_file_path}"
    except Exception as e:
        return f"サーバーエラー: {str(e)}", 500


# *****************************
# アプリケーションの起動
# *****************************
if __name__ == "__main__":
    # アップロードフォルダが存在しない場合は作成
    if not os.path.exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)
    app.run(debug=True)