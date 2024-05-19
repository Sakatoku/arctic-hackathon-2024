
# RAWデータを読み込む
def read(filename):
    # ファイルを開いてすべての行を読み込む。改行の代わりに;を追加する
    with open(filename, 'r') as f:
        return f.read().replace('\n', ';')

# RAWデータを整形する
def format(raw_str):
    # ;を区切り文字としてリストに変換する
    tag_list = raw_str.split(';')
    # 空要素を削除する
    tag_list = [tag for tag in tag_list if tag]
    # 重複要素を削除する
    tag_list = list(set(tag_list))
    return tag_list

# タグリストをプロンプトに変換する
def to_prompt(tag_list):
    prompt_template = "<will>タグで囲まれた文章は旅行中の食事に関するユーザの要望です。\n<tags>タグで囲まれたタグリストは近隣にあるレストランの属性を示します。\n最もユーザの要望を満たすと考えられるタグを選んでください。タグは必ず<tags>タグに記載されたものをそのまま出力してください。また、{{ \"result\":\"burger\" }}のようにタグのみをJSONで出力してください。\n<will>{0}</will>\n<tags>{1}</tags>"
    # タグリストをプロンプトに変換する
    user_prompt = "海鮮ピザ"
    tag_parameter = ",".join(tag_list)

    return prompt_template.format(user_prompt, tag_parameter)

# タグリストをプロンプトに変換する
def to_prompt2(tag_list):
    prompt_template = "<will>タグで囲まれた文章は旅行中の食事に関するユーザの要望です。\n<stores>情報は近隣にあるレストランの情報です。\n最もユーザの要望を満たすと考えられるレストランを選んでください。レストランは必ず<stores>タグに記載されたものをそのまま出力してください。また、{{ \"result\":\"Snowflake Pizza\" }}のようにタグのみをJSONで出力してください。\n<will>{0}</will>\n<stores>{1}</stores>"
    # タグリストをプロンプトに変換する
    user_prompt = "海鮮ピザ"

    return prompt_template.format(user_prompt, tag_list)


raw_str = read('temp/cuisine_tags_raw.txt')
tag_list = format(raw_str)
# print(tag_list)
# print(len(tag_list))

prompt = to_prompt(tag_list)
print(prompt)

# <will>タグで囲まれた文章は旅行中の食事に関するユーザの要望です。
# これを行動時間別に分割してください。
# 出力はJSON形式で行ってください。
# <will>昼は海鮮ピザ、夜はステーキと赤ワインを食べたいな。</will>


# <will>タグで囲まれた文章は旅行中の食事に関するユーザの要望です。
# <tags>タグで囲まれたキーワードリストは近隣にあるレストランの属性を示します。
# 最もユーザの要望を満たすと考えられるキーワードを3つ選んでください。
# <will>昼は海鮮ピザ、夜はステーキと赤ワインを食べたいな。</will>
# <tags>filipino,arab,moroccan,hawaiian,japanese,ramen,korean,brazilian,nabe,salad,mediterranean,italian_pizza,nepalese,fish,california,comfort_food,burmese,burger,peruvian,greek,barbecue,californian,breakfast,brunch,wings,pakistani,lebanese,cervecerﾃｭa,seafood,asian,ethiopian,salvadoran,hotpot,french,mexican,steak_house,spanish,chicken,indian,bubble_tea,italian,sandwich,pasta,german,modern,dumpling,cajun,napoletana,thai,steak,noodle,jewish,vietnamese,curry,sushi,diner,tapas,chinese,ice_cream,pinsa,taiwanese,coffee_shop,american,kebab,pizza</tags>

# 次のプロンプトは旅行プランに関する依頼です。このプロンプトを時間帯別に分割してJSON形式で出力してください。 <prompt>昼は海鮮ピザ、夜はステーキと赤ワインを食べたいな。</prompt>

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()

stores = read_file('temp/storelist.txt')
prompt = to_prompt2(stores)
print(prompt)