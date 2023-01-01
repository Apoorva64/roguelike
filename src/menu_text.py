input_text = open('menu_text.txt', 'r').readlines()
text=''

for line in input_text:
    text += line.strip('\n')+' <br>'
