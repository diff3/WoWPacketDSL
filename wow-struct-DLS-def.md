# WoW-struct DSL definition

'



## **Struktur och syntax för DSL**

* **Alla definationer måste börja med** endian: <little/big>.

* **Fält definieras i ordning och läses sekventiellt**, utan omstrukturering.

* **“Header” och “Data” är bara visuella hjälpmedel** för att strukturera definitionen, men påverkar inte parsningen.

* **Kommentarer (#) och tomma rader är tillåtna** och ignoreras av programmet.



```python
<fält_namn>: <typ> [, modifierare]

# Ex. 

cmd: B
error: B
size: H
gamename: 4s, MU
ip_address: 4s, W
```



* **Fältet kan ha ett namn eller _ om det ska ignoreras.**

* "cmd: B" betyder att fältet heter cmd och är en uint8.

* _: H betyder att det är en uint16, men parsern ignorerar det. offset kan även användas.

* Fält kan antingen ha ett namn, eller hoppas över, men alla måste ha en storlek definerad

* **Typen är i Python struct-format**, så att fältens storlek alltid är definierad.

* **Modifierare är valfria**, men kan ge extra beteenden.
* När parsern har läst och tolkat ett paket skapas **ett objekt** där **varje fält blir ett attribut**.
* Man kan då **enkelt referera till data med object.<fält_namn>**.



```python
endian: little
cmd: B
error: B
size: H
gamename: 4s, MU
ip: 4s, W

data: 0x01 0x00 0x2A 0x57 0x6F 0x57 0x00 0xC0 0xA8 0x00 0x01

output:
print(packet.cmd)      # 1
print(packet.error)    # 0
print(packet.size)     # 42
print(packet.gamename) # "WOW"  (modifierad av MU: uppercase + mirrored)
print(packet.ip)       # "192.168.0.1" (modifierad av W: tolkad som IP)
```



 **Modifierare**



**📌 Modifierare**

* Modifierare är **alltid ett tecken och kan kombineras direkt**.

* De kan skrivas **med eller utan mellanrum och kommatecken**, t.ex.: MU, M, U, M U
* De tolkas i den ordning som de står
* **< > är de enda modifierarna som påverkar ordningen**. De måste stå först
* "< M U" ✅ → Rätt (big-endian + Uppercase + Mirror).
* "M < U" ❌ → Fel (< måste stå först om det används).
* **Felaktiga modifierare ignoreras, men kan ge varning.**
* Exempel: "gamename: 4s, Z" → Parsern kan antingen ignorera Z eller ge "Unknown modifier 'Z'".
* **Om _ används, betyder det att fältet ignoreras.**
* "_: 4s, O" betyder att fältet skrivs ut men ignoreras i andra sammanhang._
* _"4s, O" är samma sak som "_: 4s, O" (valfritt att skriva _).



| **Modifier** | **Beskrivning**                                              |
| ------------ | ------------------------------------------------------------ |
| **M**        | **Mirrored** – Reverserar byteordningen för strängar/binärdata. |
| **W**        | **IP** – Tolkar byte-data som en IPv4-adress (xxx.xxx.xxx.xxx). |
| **U**        | **Uppercase** – Konverterar strängdata till versaler.        |
| **u**        | **Lowercase** – Konverterar strängdata till gemener.         |
| **O**        | **Output only** – Skriv ut fältet men hoppa över det i andra sammanhang. |
| **< >**      | **Overrule endian** – Tvingar ett enskilt fält att använda big-endian (<) eller little-endian (>), oavsett paketets endian. |

Möjligen att vi även kan inkludera data omvandling i Modifiers. Datan vi läser in är alltid binär. 

| **Typ**            | **Omvandlingsmodifierare** | **Exempel DSL**         | **Exempel resultat** |
| ------------------ | -------------------------- | ----------------------- | -------------------- |
| **Byte → Hex**     | H                          | guid: B, H              | "0x1F"               |
| **Byte → Binär**   | B                          | flags: B, B             | "0b10100101"         |
| **Byte → Int**     | I                          | count: B, I             | 32                   |
| **Byte → String**  | S                          | name: 4s, S             | "Test"               |
| **Bitmask → Int**  | I                          | flag: 4b, bitmask, I    | 15                   |
| **Bitmask → Bool** | B                          | enabled: 1b, bitmask, B | True                 |



**📌Variabler**

* Ett fält kan vara beroende av ett tidigare fält som anger dess längd.

* **Syntax för detta:**



```python
count: B
values: <count>H

length_field: B
data: <length_field>s
```



* Här säger vi att **length_field och count innehåller längden för data**.
* Parsern **måste läsa length_field först** innan den kan tolka data.




## Padding



| **Padding-syntax**   | **Beskrivning**                                  |
| -------------------- | ------------------------------------------------ |
| padding: 4           | Hoppa över **4 bytes**                           |
| padding: 3b          | Hoppa över **3 bitar**                           |
| padding: <size>      | Hoppa över size bytes (variabel storlek)         |
| padding: <size * 8>b | Hoppa över size * 8 bitar (variabel bit-padding) |



📌 **Skillnad från Python struct**

* **Python struct arbetar bara med bytes**, medan vår padding kan hantera bit-nivå.

* **Padding står nu för sig själv i DSL:et**, oberoende av struct-typerna.

* **Om bit-padding används, måste parsern hantera bit-manipulation själv.**



## Bit-mask



* **Bitmaskens fält får sin storlek från typen (B, H, etc.)**.

* **Fältens bit-positioner måste rymmas inom denna storlek**.

* **Bitar utanför typen ger fel** (t.ex. "bitmask: 0-9" på B är ogiltigt).



```python
status_flags: B, bitmask:
    is_visible: 0
    is_moving: 1
    has_target: 2
    speed: 3-4
    direction: 5-7
    
status_flags: H, bitmask:
    is_visible: 0
    is_moving: 1
    has_target: 2
    speed: 3-4
    direction: 5-7
    some_flag: 8
    another_flag: 9
    
packet.status_flags.is_visible   # False (bit 0 = 0)
packet.status_flags.is_moving    # True  (bit 1 = 1)
packet.status_flags.has_target   # False (bit 2 = 0)
packet.status_flags.speed        # 2 (bitar 3-4 = '10')
packet.status_flags.direction    # 5 (bitar 5-7 = '101')
```



## Loops



- <count> kan vara en siffra eller en variabel**

- **Allt under loopen indenteras enligt Python-syntax**

- **Ingen avslutande tagg behövs**
- **Loopar fungerar som en sekventiell upprepning av fält.**
-  **Syntax: loop <count> as <name>:**
-  **Alla iterationer lagras som dictionaries i en lista.**
-  **Om count = 0, körs loopen inte.**
-  **Om count är negativt, kastar parsern fel.**
-  **Loopar fungerar utan avslutande tagg – indentering styr.**
-  **Om vi stöter på nested loops i framtiden, hanterar vi dem som vanliga loopar.**



```python
loop 3 as realms:
    realm_id: H
    realm_name: 32s
    
realm_count: B
loop <realm_count> as realms:
    realm_id: H
    realm_name: 32s
    
packet.realms = [
    {"realm_id": 1024, "realm_name": "Realm One"},
    {"realm_id": 2048, "realm_name": "Realm Two"},
    {"realm_id": 4096, "realm_name": "Realm Three"}
]

print(packet.realms[0]["realm_id"])  # 1024
print(packet.realms[1]["realm_name"])  # "Realm Two"
```





**📌 Sammanfattning av bitläsning i randseq med bitmask**



- **randseq definierar en sekvens av bytes där datan hämtas i en specifik ordning.**

- **Vissa fält kan vara bitmasker, andra kan vara vanliga bytes.**

-  **Vi återanvänder bitmask-syntaxen för bitläsning i randseq** → Mer konsekvent DSL.

- **Bitfält definieras inuti bitmask-blocket och anger vilka bitar som används.**

- **Fält kan vara enskilda flaggor (1 bit) eller ett heltal (flera bitar).**

- **Fält hämtas från sin angivna position i randseq och lagras i variablerna i samma ordning.**
- **Om en variabel är en lista (guid, guild_guid), fylls den i den ordningen som anges.**



```python
randseq 19:
    guid: 6 1 3 7 4 16 13
    guild_guid: 12 11 17 2 0 18 8 14
    name_data: 9b, bitmask:
        name_len: 0-5   # Läs 6 bitar från byte 9
        is_special: 6   # En enskild flagga (True/False)
        extra_flag: 7   # En annan flagga

packet.guid = ["g", "b", "d", "h", "e", "q", "n"]
packet.guild_guid = ["m", "l", "r", "c", "a", "s", "i", "o"]        
packet.name_len = 43  # (bit 0-5 = 101011)
packet.is_special = True  # (bit 6 = 1)
packet.extra_flag = False  # (bit 7 = 0)
```





**📌 Alternativ 1: Allt i en databas**



**Struktur:**

​	•	**En enda tabell för alla paketdata** (packet_definitions, packet_data, expected_output lagras i samma rad som BLOBs).

​	•	**Alla tre filtyper (.def, .bin, .bson) lagras som BLOBs i databasen.**



**Fördelar:**

​	•	**Enkel uppslagning** – Alla data finns på ett ställe (en SQL-databas).

​	•	**Snabbare åtkomst** – En enda SQL-query för att hämta alla delar av paketet.

​	•	**Effektiv hantering av data** – Ingen filhantering i operativsystemet.

​	•	**Fördel vid hög dataproduktion** – Inga diskfiloperationer behövs, snabbt och effektivt.



**Nackdelar:**

​	•	**Större databasstorlek** – Om rådata är stor kan databasen växa snabbt.

​	•	**Behöver extra funktionalitet för att hantera stora BLOBs** (kan vara långsamt vid mycket stora paket).



------



**📌 Alternativ 2: En fil per paketdefinition (.def, .bin, .bson)**



**Struktur:**

​	•	**Varje paketdefinition och relaterad data lagras i separata filer** i en mappstruktur.



```bash
/definitions/
└── AUTH_LOGON_CHALLENGE.def
/data/
└── AUTH_LOGON_CHALLENGE.bin
/expected_output/
└── AUTH_LOGON_CHALLENGE.bson
```

**Fördelar:**

​	•	**Enkel filstruktur** – Varje paket har sin egen uppsättning av filer, vilket gör det lätt att hantera och redigera.

​	•	**Lätt att uppdatera eller lägga till nya paket** utan att påverka andra delar.

​	•	**Filhantering via operativsystemet** kan vara snabbare vid små dataset.



**Nackdelar:**

​	•	**Kan bli mycket filhantering** – Om antalet filer blir stort (exempelvis 4500 filer) kan det bli oöverskådligt.

​	•	**Fler filoperationer vid uppstart** – Om många paket är involverade, kan det vara långsamt att öppna och läsa alla filer.



------



**📌 Alternativ 3: Hybrider av fil (grupperade)**



**Struktur:**

​	•	**Filer är grupperade efter pakettyper** (t.ex. AUTH, WORLD), där varje grupp har både .def, .bin, och .bson för relevanta paket.



```bash
/AUTH/
└── AUTH_LOGON_CHALLENGE.defbson
└── AUTH_LOGON_PROOF.defbson
/WORLD/
└── WORLD_MESSAGE.defbson
```





**Fördelar:**

​	•	**Mindre filhantering än 4500 filer** – Men ändå lätt att hålla grupperade paket för olika ändamål.

​	•	**Tydlig uppdelning** – Paket från samma kategori hålls samman, vilket gör det enklare att hantera.

​	•	**Snabbare uppstart** – Kan läsa in en hel mapp (t.ex. alla AUTH-paket) istället för att öppna många individuella filer.



**Nackdelar:**

​	•	**Kräver lite mer organisering** – Om grupperingen inte är korrekt kan det bli svårt att hitta rätt paket snabbt.

​	•	**Större filer** – Om .def och .bson ligger tillsammans i samma fil, kan det vara svårt att separera dem vid behov.



------



**📌 Slutsats**

​	•	**En databas** är mest fördelaktig om du vill ha **effektiv uppslagning och lätt hantering av stora datamängder**, men det kan kräva mer **komplexitet för att hantera stora BLOBs**.

​	•	**En fil per paketdefinition** är bäst om du **inte har problem med filhantering och vill ha snabb överblick**.

​	•	**Grupperade filer** är ett bra **mellanalternativ** om du vill ha en balans mellan effektivitet och hanterbarhet.
