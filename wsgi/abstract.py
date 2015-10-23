import html;
import string;
import tornado.escape;

def gen_text_abstract(text, truncate_len, *, placeholder = '[...]'):
    L = len(text);
    if truncate_len >= L:
        return (text, False);
    i = 0;
    pos = truncate_len;
    if text[pos] in string.ascii_letters:
        while pos > 0 and text[pos - 1] in string.ascii_letters:
            pos -= 1;
    while pos > 0:
        s = text[pos - 1: pos + 2];
        if s == '\\(' or s == '\\)' or s == '\\[' or s == '\\]' or s == '$$':
            pos -= 1;
        else:
            break;
    s_stack = [];
    i = 0;
    while i < pos:
        if i == pos - 1:
            break;
        s = text[i: i + 2];
        if s == '\\)' or s == '\\]' or (s == '$$' and len(s_stack) != 0):
            s_stack.pop();
            i += 2;
        elif s == '\\(' or s == '\\[' or s == '$$':
            s_stack.append(i);
            i += 2;
        else:
            i += 1;
    if len(s_stack) != 0:
        pos = s_stack[0];
    return (text[:pos] + placeholder, True);

#
# generates abstracts given a complete sequence of HTML
#
# abstract_len is the number of characters to be reserved in the abstract

def gen_html_abstract(html_content, abstract_len, *, placeholder = '[...]'):
    def last_valid_char(s):
        i = len(s) - 1;
        while i >= 0 and s[i] in '\t\n\r ':
            i -= 1;
        if i < 0:
            return '';
        return s[i];

    def first_valid_char(s):
        L = len(s);
        i = 0;
        while i < L and s[i] in '\t\n\r ':
            i += 1;
        if i == L:
            return '';
        return s[i];

    parts = html_content.split('<');
    seq = [];
    for p in parts:
        sp = p.split('>', 1);
        if len(sp) == 2:
            seq.append((0, sp[0])); # tag
            seq.append((1, tornado.escape.xhtml_unescape(sp[1]))); # data
        else:
            seq.append((1, tornado.escape.xhtml_unescape(sp[0])));
    rem = abstract_len;
    tag_stack = [];
    exceeded = False; # exceeded the abstract_len limit or not
    out = [];
    try:
        for s in seq:
            if s[0] == 0: # is a tag
                he = first_valid_char(s[1]);
                ta = last_valid_char(s[1]);
                if he == '/': # is an end tag
                    if tag_stack[len(tag_stack) - 1][1]: # corresponds a visible start tag
                        out.append('<' + s[1] + '>');
                    tag_stack.pop();
                elif ta == '/': # is a start-end tag
                    if not exceeded:
                        out.append('<' + s[1] + '>');
                else: # is a start tag
                    if not exceeded: # should be visible
                        out.append('<' + s[1] + '>');
                        tag_stack.append((s[1], True));
                    else: # should not be visible, merely in order to correspond the close tag
                        tag_stack.append((s[1], False));
            elif not exceeded: # is data
                abt = gen_text_abstract(s[1], rem);
                out.append(tornado.escape.xhtml_escape(abt[0]));
                if abt[1]:
                    exceeded = True;
                else:
                    rem -= len(s[1]);
    except:
        raise ValueError('Invalid HTML format!');
    if len(tag_stack) != 0:
        raise ValueError('Invalid HTML format!');
    return ''.join(out);

  #  for s in seq:
  #      print(s);

#print(gen_html_abstract('<a>Href</a><p><b>Hello world! Hello world!</b></p>', 10)); # for test

