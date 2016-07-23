import sass
import spacy
from spacy.en import English

from collections import defaultdict

from flask import Flask
from flask import request
app = Flask(__name__)

# Instantiate parser (in this case SpaCy)
nlp = English()


def parse_sentence(sent):
    return nlp(sent)


def build_dependency_tree(tokens):
    pass


def navigate_tree(root, output, depth=0):
    output[root] = []
    for sub in root[1].children:
        output[root[0]].append(sub[0])
        navigate_tree(sub, output, depth + 1)


def get_root(labelled_tokens):
    found = False
    for tok in labelled_tokens:
        # @TODO: if tok has property dep_
        if tok.dep_.lower() == u"root":
            found = True
            break
    if found:
        return tok
    return None

##############################################################################
#
##############################################################################

@app.route("/")
def hello():
    return "Hello World!"


@app.route("/syntree", methods=['GET', 'POST'])
def syntree():

    sentence = request.args.get('sentence', "Robots in popular_culture are there to remind us of the_awesomeness of unbounded_human_agency")
    tokens = parse_sentence(sentence)

    tokens_index_map = {}
    for i, tok in enumerate(tokens):
        tokens_index_map[tok.idx] = i

    # labelled_tokens = [(i, tok) for i, tok in enumerate(tokens)]

    root = get_root(tokens)

    connected = defaultdict(list)
    conn_matrix = defaultdict(dict)

    def word_adjacency(root, output):
        output[tokens_index_map[root.idx]] = []
        for sub in root.children:
            output[tokens_index_map[root.idx]].append((tokens_index_map[sub.idx], sub))
            word_adjacency(sub, output)

    word_adjacency(root, connected)

    levels = -9999999
    for c in connected.keys():
        for s, tok in connected[c]:
            conn_matrix[c][s] = tok
            levels = max(levels, abs(c - s))
    print("Max level: {}".format(levels))

    # 100% / $words;

    number_of_words = len(tokens)
    sass_string = """

        /* Variables */
        $words:  """ + str(number_of_words) + """;
        $levels: """ + str(levels) + """;
        $background: white;
        $color: black;
        $arrow-arch: 3px;
        $arrow-head: 18px;
        $arrow-width: 175px;
        $arrow-height: 100% / $levels;
        $height: 30vw;

        #displacy .arrow:before, #displacy .word:after {
            font-family: "Work Sans", "Arial Black", Gadget, sans-serif
        }

        #displacy .arrow:before, #displacy .word:after {
            font-size: 1.0rem;
            line-height: 1.375;
            font-weight: normal;
            text-transform: uppercase
        }

        #displacy *,#displacy *:before,#displacy *:after{
            box-sizing:border-box
        }

        #displacy{
            position:relative;overflow:scroll
        }

        #displacy .focus{
            position:absolute;
            top:0;
            height:100%;
            z-index:-1;
            background:rgba(0,0,0,.25)
        }

        #displacy .current-stack{
            margin:6em 1.5em;
            font-size:.75em;
            opacity:.25
        }

        #displacy .actions{
            position:fixed;
        }

        #displacy .words{
            display:flex;
            display:-webkit-flex;
            display:-ms-flexbox;
            display:-webkit-box;
            flex-flow:row nowrap;
            overflow:hidden;
            text-align:center
        }

        #displacy .words .word:after{
            content:attr(title);
            display:block
        }

        #displacy .arrows{
            width:100%;
            position:relative
        }

        .level{
            position:absolute;
            bottom:0;
            width:100%
        }

        #displacy .arrow{
            height:100%;
            position:absolute;
            overflow:hidden
        }

        #displacy .arrow:before{
            content:attr(title);
            text-align:center;
            display:block;
            height:200%;
            border-radius:50%;
            border:2px solid;
            margin:0 auto
        }

        #displacy .arrow:after{
            content:'';
            width:0;
            height:0;
            position:absolute;
            bottom:-1px;
            border-top:12px solid;
            border-left:6px solid transparent;
            border-right:6px solid transparent
        }

        #displacy .arrow.null{
            display:none
        }







        #displacy .arrows {
            height:175px
        }

        #displacy .level {
            left:calc(175px/2)
        }

        @for $i from 1 through $levels {
            #displacy .level#{$i} { height: #{$arrow-height * $i} }
            #displacy .level#{$i} .arrow { width:calc(175px * #{$i})}
            #displacy .level#{$i} .arrow:before {width:calc(100% - 10px * #{$levels - $i} - 10px)}
            #displacy .level#{$i} .arrow.left:after {left:calc(10px * #{($levels - $i) * (1 / ($levels - 1))})}
            #displacy .level#{$i} .arrow.right:after {right:calc(10px * #{($levels - $i) * (1 / ($levels - 1))})}
        }

        @for $i from 1 through $words {
            #displacy .level .arrow:nth-child(#{$i}){ left:calc(175px * #{$i - 1}) }
        }

        #displacy .words{min-width:calc(175px * #{$words})}

        .words .word {
            width:175px
        }

    """
    css_str = sass.compile(string=sass_string)

    opening_arrows = '<div class="arrows">'
    closing_arrows = '</div>'

    draw_arrow_at = defaultdict(dict)
    for key, conn in connected.items():
        for c, tok in conn:
            level = abs(key - c)
            if key in draw_arrow_at[level]:
                draw_arrow_at[level][key].append(c)
            else:
                draw_arrow_at[level][key] = [c]

    html = "<html>"

    html += """
    <head>
        <title>NLTree Demo</title>
        <meta charset="utf-8">
        <link rel="stylesheet" href="./static/css/arrows/arrows-style.css">
    </head>
    """

    html += "<body>"
    html += '<div id="displacy">'

    html += '<style class="" scoped="true">'
    html += css_str
    html += '</style>'

    html += '<div class="container">'

    """
    for level in range(number_of_words - 1):
        pairs = set()
        for i in range(number_of_words - level - 1):
            pairs.add((i, i + level + 1))
        print(pairs)
    """

    html += opening_arrows
    levels_html = ["" for _ in range(number_of_words - 1)]
    for level in range(number_of_words - 1):
        levels_html[level] = ""
        mapping = draw_arrow_at[level + 1]

        pairs = []
        for i in range(number_of_words - level - 1):
            pairs.append([i, i + level + 1])

        for p in pairs:
            if p[0] in mapping and p[1] in mapping[p[0]]:
                title = conn_matrix[p[0]][p[1]].dep_
                levels_html[level] += '<span class="arrow right" title="{}"></span>\n'.format(title)
            elif p[1] in mapping and p[0] in mapping[p[1]]:
                title = conn_matrix[p[1]][p[0]].dep_
                levels_html[level] += '<span class="arrow left" title="{}"></span>\n'.format(title)
            else:
                levels_html[level] += '<span class="arrow null"></span>\n'

        html += '<div class="level level{}">'.format(level + 1)
        html += levels_html[level]
        html += '</div>'
    html += closing_arrows

    html += '<div class="words">'
    for tok in tokens:
        html += """
        <div class="word w-noun" title="{}">
            <span class="">{}</span>
        </div>
        """.format(tok.tag_, tok.orth_)
    html += '</div>'

    html += "</div>"
    html += "</body></html>"

    return html


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5501)
