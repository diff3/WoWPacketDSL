import re

object = {
    'realm_list_size': 2
}

REALM_LIST_S = """
endian: little
header:
    cmd: B
    size: H
    realm_list_size: IH
data:
    loop <realm_list_size> as realmlist:
        icon: B
        lock: B
        flag: B
        name: S
        address: S
        pop: f
        characters: B
        timezone: B
        realmid: B
    unk2: B
    unk3: B
"""

i = 0

lines = REALM_LIST_S.split("\n")

while len(lines) > i:
    if 'loop' in lines[i]:
        leading_spaces = len(re.match(r"^\s*", lines[i])[0])
       
        loop_match = re.match(r"loop <(.*?)> as (\w+):", lines[i].strip())

        if loop_match:
            loop_count = object[loop_match.group(1)]
            loop_name = loop_match.group(2)
            object[loop_name] = []

            field_count = 0
            n = i + 1 
            
            print(len(re.match(r"^\s*", lines[n])[0]))
            while n < len(lines) and len(re.match(r"^\s*", lines[n])[0]) > leading_spaces:
                field_count += 1
                n = n + 1 
            
            print(f"Number of fields in the loop: {field_count}")

            cleaned_lines = [line.lstrip() for line in lines[i + 1:i + field_count + 1]]
            cleaned_lines = "\n".join(cleaned_lines)


            for x in range(loop_count):
                object[loop_name].append(cleaned_lines)
            
            i += field_count + 1

        print(object)
    else:
        print(lines[i])
        i += 1  




"""
            object[loop_name] = []

            for n in range(loop_count):
                object[loop_name].append({'realmid': n, 'realmname': 'realm_one'})
                object[loop_name].append({'realmid': n, 'realmname': 'realm_two'})

            print(object)
            print(object['realmlist'])
            print(object['realmlist'][0]['realmid'])
            print(object['realmlist'][1]['realmname'])
    print(lines[i])
    i += 1"""
