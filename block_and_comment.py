import re

class WoWStructParser:

    @staticmethod
    def handle_comments_and_blocks(lines, i):
        """
        Hanterar både kommentarer och block. Identifierar kommentarer som startar med # eller #- och slut på samma rad eller efter flera rader.
        Hanterar också block som loop, if, switch, bitmask och randseq.
        """
        

        print(lines)
        line = lines[i].strip()


        print(line)
        # Kontrollera för flerradig kommentar
        if line.startswith("#-"):
            print("här nu")
            comment_lines = []
            # Lägg till första raden
            comment_lines.append(line)
            i += 1
            # Läs tills slutkommentaren (-#)
            while not lines[i].strip().endswith("-#"):
                comment_lines.append(lines[i].strip())
                i += 1
            # Lägg till slutkommentaren
            comment_lines.append(lines[i].strip())
            return comment_lines, i + 1  # Returnera alla kommentarlinjer och nästa rad
        
        # Kontrollera enkelradskommentar (alles efter # tas bort)
        elif "#" in line:
            print("tar port allt")
            return [line.split("#")[1].strip()], i + 1
        
        # Hantera block och loopar
        elif re.match(r"loop <(.*?)> as (\w+):", line):  # Hantera loop
            return WoWStructParser.handle_loop(lines, i)

        elif re.match(r"block (.*?)\s*:", line):  # Hantera block
            return WoWStructParser.handle_loop(lines, i)
        
        elif re.match(r"if <.*?>:", line):  # Hantera if-sats
            return WoWStructParser.handle_if(lines, i)

        elif re.match(r"switch <.*?>:", line):  # Hantera switch-sats
            return WoWStructParser.handle_switch(lines, i)
        
        # Om inget matchar, returnera den aktuella raden
        return [line], i + 1

    @staticmethod
    def handle_loop(lines, i):
        """Hantera loopar och räkna antalet indenterade rader"""
        loop_lines = [lines[i].strip()]
        leading_spaces = len(re.match(r"^\s*", lines[i])[0])
        i += 1
        
        while i < len(lines) and len(re.match(r"^\s*", lines[i])[0]) > leading_spaces:
            loop_lines.append(lines[i].strip())
            i += 1

        return loop_lines, i  # Returnera loopens linjer och nästa rad
    
    @staticmethod
    def handle_block(lines, i):
        """Hantera block"""
        block_lines = [lines[i].strip()]
        leading_spaces = len(re.match(r"^\s*", lines[i])[0])
        i += 1

        while i < len(lines) and len(re.match(r"^\s*", lines[i])[0]) > leading_spaces:
            block_lines.append(lines[i].strip())
            i += 1

        return block_lines, i  # Returnera blockets linjer och nästa rad

    @staticmethod
    def handle_if(lines, i):
        """Hantera if-sats"""
        if_lines = [lines[i].strip()]
        leading_spaces = len(re.match(r"^\s*", lines[i])[0])
        i += 1

        while i < len(lines) and len(re.match(r"^\s*", lines[i])[0]) > leading_spaces:
            if_lines.append(lines[i].strip())
            i += 1

        return if_lines, i  # Returnera if-satsens linjer och nästa rad

    @staticmethod
    def handle_switch(lines, i):
        """Hantera switch-sats"""
        switch_lines = [lines[i].strip()]
        leading_spaces = len(re.match(r"^\s*", lines[i])[0])
        i += 1

        while i < len(lines) and len(re.match(r"^\s*", lines[i])[0]) > leading_spaces:
            switch_lines.append(lines[i].strip())
            i += 1

        return switch_lines, i  # Returnera switch-satsens linjer och nästa rad


lines = """
loop:
    cmd: B
    test: B
test: A
"""


print(lines[1])



test = WoWStructParser.handle_comments_and_blocks(lines.split('\n'), 1)

print(test)