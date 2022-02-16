# メインの処理（62行目のwakati以降）は下のサイトを参考にした
# https://qiita.com/k-jimon/items/f02fae75e853a9c02127
import re
import MeCab
from collections import deque
import random
import twint
from datetime import datetime, timedelta
import pandas as pd


def get_tweet( u_name, before=3 ):
    # Configure
    c = twint.Config()
    c.Username = u_name
    # c.Search = "カーリング"
    # c.Min_likes = 1000
    c.Lang = "ja"
    c.Pandas = True
    c.Hide_output = True

    today = datetime.today()
    start = today - timedelta(days=before)
    c.Since = datetime.strftime(start, '%Y-%m-%d')

    # Run
    twint.run.Search(c)

    # save to csv
    Tweets_df = twint.storage.panda.Tweets_df
    Tweets_df.to_csv("tweets.csv")


def csv2txt():
    df = pd.read_csv("./tweets.csv", encoding='utf-8')
    df2 = df["tweet"]
    f = open("not_standardized.txt", "w", encoding='utf-8')
    for _ in df2[1:]:
        f.write(f"{_}\n")
    f.close()


def standardize():
    f = open("standardized.txt", "w", encoding="utf-8")
    with open("not_standardized.txt", encoding='utf-8') as data:
        for line in data:
            text = line.replace('\n', "。")
            if text != "" and "https" not in text and "@" not in text:
                text = text.replace(" ", "。")
                f.write(f"{text}\n")
    f.close()


def load_text( txt_path ):
    res = ""
    with open(txt_path, encoding='utf-8') as data:
        for d in data:
            res += d.rstrip("\n").replace("　", "")
        return res


def wakati( text ):
    tagger = MeCab.Tagger("-Owakati")
    parsed_text = ""
    for one_line_text in one_sentence_generator(text):
        parsed_text += " "
        parsed_text += tagger.parse(one_line_text).rstrip("\n")
    wordlist = parsed_text.split(" ")
    return wordlist


def one_sentence_generator( long_text ):
    sentences = re.findall(".*?。", long_text)
    for sentence in sentences:
        yield sentence


def make_model( text, order=2 ):
    model = {}
    wordlist = wakati(text)
    queue = deque([], order)
    queue.append("[BOS]")
    for markov_value in wordlist:
        if len(queue) < order:
            queue.append(markov_value)
            continue

        if queue[-1] == "。":
            markov_key = tuple(queue)
            if markov_key not in model:
                model[markov_key] = []
            model.setdefault(markov_key, []).append("[BOS]")
            queue.append("[BOS]")
        markov_key = tuple(queue)
        model.setdefault(markov_key, []).append(markov_value)
        queue.append(markov_value)
    return model


def make_sentence( model, sentence_num=5, seed="[BOS]", max_words=1000 ):
    sentence_count = 0

    key_candidates = [key for key in model if key[0] == seed]
    if not key_candidates:
        print("Not find Keyword")
        return
    markov_key = random.choice(key_candidates)
    queue = deque(list(markov_key), len(list(model.keys())[0]))

    sentence = "".join(markov_key)
    for _ in range(max_words):
        markov_key = tuple(queue)
        next_word = random.choice(model[markov_key])
        sentence += next_word
        queue.append(next_word)

        if next_word == "。":
            sentence_count += 1
            if sentence_count == sentence_num:
                break
    return sentence


def main():
    u_name = "itsuki_jpnlonvn"
    get_tweet(u_name, before=200)
    csv2txt()
    standardize()
    text = load_text("standardized.txt")
    model = make_model(text, order=2)
    sentence = make_sentence(model, sentence_num=10)
    res = sentence.split("[BOS]")
    print(*res, sep="\n")


if __name__ == '__main__':
    main()
