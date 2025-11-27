Ja, daar zijn een paar dingen waar je vanaf nu bewust op moet letten – precies omdat jullie model nu iets complexer en multi-company is.

Ik splits het even op in “belangrijk voor de prof / verslag” en “praktische valkuilen in de code”.

1. Belangrijkste punt: consistentie van het bedrijf bij Item

Je hebt nu:

Material → heeft company_name

Zone → heeft company_name

Item → heeft alleen material_id en zone_id

De database controleert niet dat:

material.company_name == zone.company_name


Dus technisch kan je een Item maken met:

material_id van bedrijf A

zone_id van bedrijf B

PostgreSQL vindt dat gewoon oké.

👉 Wat doe je daaraan?

Twee dingen:

In je applicatielogica (Flask-routes / forms):

Bij het aanmaken/bewerken van een Item:

haal de Material op

haal de Zone op

check: material.company_name == zone.company_name == current_user.company_name

Als dat niet klopt → foutmelding geven.

In je verslag kun je kort vermelden:

Dat dit een businessregel is die in de applicatielaag wordt afgedwongen, niet in de database, en waarom (composite FKs zouden het model complexer maken).

Voor een schoolproject is dat perfect verdedigbaar.

2. Scoping op basis van current_user.company_name

Heel belangrijk wanneer je queries schrijft:

Toon nooit zomaar alle materialen/items/zones, maar altijd gefilterd op het bedrijf van de ingelogde user.

Bijvoorbeeld:

# Materials van het bedrijf van de user
Material.query.filter_by(company_name=current_user.company_name).all()

# Zones van dit bedrijf
Zone.query.filter_by(company_name=current_user.company_name).all()

# Items van dit bedrijf (via join op material)
Item.query.join(Material).filter(Material.company_name == current_user.company_name).all()


En voor reservations:

# Alleen eigen reservaties tonen:
Reservation.query.filter_by(username=current_user.username).all()


Of, als je ooit alle reservaties binnen een bedrijf wilt tonen:

Reservation.query.join(Reservation.item).join(Item.material).filter(
    Material.company_name == current_user.company_name
).all()


Valkuil: als je vergeten filtert op company_name, kunnen users in theorie elkaars data zien als er ooit meerdere companies bijkomen.

3. Businesslogica rond voorraad / reservations

De database checkt alleen:

quantity in Item is NOT NULL

quantity in Reservation is NOT NULL

Maar hij checkt niet:

Of de som van alle reservations ≤ Item.quantity

Of quantity in reservation > 0

Of je geen negative stock creëert

Dat moet je dus ook in je code doen, bijvoorbeeld:

# Voor je een reservation aanmaakt / wijzigt:
reserved_qty = db.session.query(db.func.sum(Reservation.quantity)).filter_by(
    item_id=item_id
).scalar() or 0

if reserved_qty + nieuwe_reservering > item.quantity:
    # fout: niet genoeg voorraad


Dat is niet per se verplicht voor de opdracht, maar het is goed om te weten dat de database je daar niet in beschermt.

4. Globaliteit van usernames

In je model:

username = db.Column(db.String, primary_key=True)


→ Usernames zijn globaal uniek, niet per bedrijf.

Dat is op zich oké (en makkelijk), maar:

Twee verschillende bedrijven kunnen niet allebei een user admin hebben.

Als je prof vraagt: zijn users per bedrijf uniek of globaal?
→ hier zijn ze globaal.

Dat is geen fout, gewoon een ontwerpkeuze waar je je bewust van moet zijn.

####




Helemaal goed, laten we dit “architectuurverhaal” even netjes uitwerken zodat je het zo kan gebruiken in je mondelinge verdediging.

1. Globale opzet: MVC-achtig, maar simpel gehouden

Ik heb alles opgekuist met het idee:

Models (models.py)
Database-structuur: Material, Zone, Item, Reservation.

Routes (routes.py)
“Controller”: alle business-logica en queries zitten hier.

Templates (base.html, inventory.html, add_item.html, use_item.html, edit_item.html, edit_material.html)
“View”: zo weinig mogelijk logica, vooral presentatie.

Belangrijk argument:

We wilde de layout exact houden zoals in Figma en zoals jij die goedgekeurd hebt.
Daarom heb ik alleen de routes opgeschoond, en de templates qua structuur niet verder opgesplitst, om geen subtiele CSS-/layout bugs te introduceren.

2. Waarom precies deze HTML-files?
2.1 base.html – de “app shell”

Rol

Bevat alles wat op alle pagina’s hetzelfde is:

Zwarte topbar met “Primetals”, login-tekst en de drie iconen (search / add / cart).

Links de “Brands” sidebar (titel + uitlegtekst).

Rechts het hoofdgedeelte waar inhoud van elke pagina komt.

Definieert drie hoofdbrokken met {% block %}:

sidebar

header

content

Redenering

Dit voorkomt duplicatie: we hoeven de topbar, sidebar-container en basis-layout niet in 5 verschillende templates te kopiëren.

Het maakt de andere templates dun: die beschrijven enkel wat er in de blocks moet, niet de volledige pagina.

Waarom geen extra partials voor bv. de topbar?

De topbar is maar op één manier aanwezig in de applicatie, er zijn geen variaties.

Een extra Jinja-partial zou complexer worden om te laden, maar niets hergebruiken in de praktijk.
→ Overkill voor een project van deze grootte.

2.2 inventory.html – het hoofdscherm

Rol

Dit is de centrale view waar alles samenkomt:

links: brands + type/description-lijst

midden: inventory cards per item

rechts (in panel): search & filter

rechts (in panel): reservations “cart”

Gebruikt alle data die inventory() in routes.py klaarzet.

Structuur intern

{% block sidebar %}

Rendered de brand-lijst en de type-description per brand.

Hier hebben we expres geen aparte template van gemaakt, omdat deze sidebar:

alleen in de inventory-view voorkomt;

rechtstreeks dezelfde query-parameters gebruikt (brand, material_id) die ook de items bepalen.

{% block header %}

Toont de titel: BRAND — TYPE of gewoon Inventory.

Rechts de drie iconen (search, add, cart) die de panels of pagina’s openen.

Deze header is uniek voor de inventory-pagina; andere pagina’s hebben eigen titel.

{% block content %}

Rendered de item-cards:

bovenaan Purpose / Packaging / Zone

dan Quantity en Reserved quantity

“More details” → toont Price + Lifecycle + Comment

Rechts de “Use”-knop.

Onder de lijst:

Search & Filter panel (HTML voor het rechter uitklap-paneel)

Reservations panel (winkelmandje)

Waarom search & filter en reservations in dezelfde file?

Functioneel horen ze bij dit scherm:

De search-filters werken rechtstreeks op de inventory()-route via query-parameters.

Het reservations-panel toont dezelfde items / materials en wordt ook alleen vanaf deze pagina gebruikt.

Technisch:

Beide panels gebruiken CSS-classes die volledig verweven zijn met de layout van inventory.html.

Door ze hier te laten staan:

hou je de HTML van dit scherm op één plek;

voorkom je dat je partials moet maken die toch enkel op één plek gebruikt worden.

Verdedigbaar argument in je mondeling:
“We hebben ervoor gekozen om alle UI-onderdelen van het inventory-scherm in één template te houden, omdat ze zowel visueel als functioneel één geheel vormen: de sidebar, de cards, de filters en het reservatiepaneel worden altijd samen gebruikt en delen dezelfde route en CSS-structuur.”

2.3 Form-pagina’s: add_item.html, use_item.html, edit_item.html, edit_material.html

Gezamenlijke principes

Alle vier:

Extenden base.html → zelfde topbar & sidebarcontainer.

Gebruiken een overlay-style (body_class / grijze achtergrond) om visueel duidelijk te maken: “je zit in een dialoogscherm”.

Plaatsen één form-card rechts, in dezelfde stijl als Figma.

Redenering:

Elke actie heeft een eigen, duidelijk scherm met een specifiek doel. Dat is gebruiksvriendelijker en eenvoudiger uit te leggen in de code dan één mega-template met allemaal if/else-blokken.

add_item.html

Doel: nieuw materiaal + nieuw item toevoegen.

Layout:

Sectie Material (brand, type, description, price, lifecycle).

Sectie Inventory item (quantity, zone, purpose, packaging, comment).

Koppeling met routes.py:

add_item() leest rechte de form fields uit deze template.

Creëert indien nodig nieuw Material en Zone, daarna een Item.

Waarom aparte template?

De layout en velden zijn uniek, worden nergens anders herhaald.

Als je dit in inventory.html zou proppen, krijg je enorm veel vertakte logica en breek je de Figma-flow (pop-up is bij Figma een apart schermoverlay).

use_item.html

Doel: een reservation toevoegen voor één Item.

Layout:

Titel “Use item”

Material title + description

“Available: X”

Form met User, Project, Quantity.

Koppeling:

use_item() route maakt een Reservation en stuurt je daarna terug naar inventory() met de juiste brand + material_id (zodat je terugkomt op het juiste item).

Waarom apart?

De flow "Use/Reserve" is conceptueel een andere taak dan “edit item”.

UI is simpeler, andere velden.

Zo kun je in je verslag netjes zeggen: “We onderscheiden drie soorten acties: toevoegen, reserveren, en bewerken. Elke actie heeft een dedicated template.”

edit_item.html

Doel: eigenschappen van een bestaand item aanpassen:

Zone, Purpose, Packaging, Comment.

Layout:

Bovenaan Material-titel + description als context.

Daaronder het kleine form.

Koppeling:

edit_item() in routes zoekt bijbehorende Zone en update het Item.

edit_material.html

Doel: materiaalgegevens wijzigen:

Brand, Type, Description, Lifecycle, Price.

Layout:

Simpel form in de rechterkolom, overlay-stijl vergelijkbaar met de andere forms.

Koppeling:

edit_material() update puur de Material-rij en redirect naar inventory met dezelfde brand/material.

3. Waarom geen extra templates / partials?

Samengevatte verdedigbare redenen:

Scope van het project

Je hebt een beperkt aantal views (1 grote + 4 forms).

Extra partials (bv. voor een card of sidebar) zouden weinig hergebruik hebben en vooral complexiteit toevoegen.

Sterke koppeling aan CSS en Figma-layout

inventory.html is 1-op-1 gemapt op het Figma-scherm:

links: brands

midden: cards

rechts: panels

Als je dit in kleinere templates zou opknippen, moet je heel goed opletten dat alle CSS-hooks (.item-card, .side-panel, …) precies hetzelfde blijven.

Omdat de UI nu exact is zoals je wil, was het veiliger om de HTML-structuur zo te laten en alleen de Python-kant op te schonen.

Duidelijke functional separation in de routes in plaats van in de templates

We scheiden de verantwoordelijkheid vooral in routes.py:
inventory, add_item, use_item, edit_item, edit_material, update_quantity, delete_reservation.

In je mondeling kan je zeggen:

“We hebben gekozen voor een scheiding per use-case in de routes, en per scherm in de templates. Verdere opsplitsing van de HTML in kleinere componenten zou meer technische complexiteit geven zonder duidelijke functionele winst.”

4. Mogelijke “flaws” / verbeterpunten die je eerlijk kan vermelden

Altijd goed om in een verdediging ook kritisch te zijn:

Herbruikbare componenten ontbreken

De kaart-layout voor items wordt nu één keer in inventory.html gedefinieerd.

In een grotere applicatie zou je daar Jinja-macros of component-templates van maken (bijvoorbeeld _item_card.html).

Hier is het niet gedaan omdat er maar één scherm is dat die kaarten gebruikt.

Overlays voor add/use/edit zijn niet pure modals

Technisch zijn add_item, use_item, edit_item, edit_material aparte pagina’s met een grijze achtergrond, geen modals bovenop inventory.

Dat is eenvoudiger te implementeren dan echte modals die via JavaScript content inladen, en het voldoet aan de Figma-look.

Maar je kan eerlijk zeggen: “Een volgende iteratie zou dit kunnen ombouwen naar echte modals om contextverlies nog verder te beperken.”

Brand-sidebar is niet verstopt op formpagina’s

Op form-pagina’s blijft links de “Brands”-kolom leeg of ongebruikt.

Functioneel stoort dat niet, maar qua UX kun je beargumenteren dat het netter zou zijn om de sidebar daar te verbergen.

Om layout-stabiliteit en eenvoud te bewaren is dat nu niet gedaan.

Filters zijn alleen op inventory

De search & filter panelen zijn hard gekoppeld aan het inventory-scherm.

Als je ooit b.v. een aparte “report”-pagina zou maken, kun je die panelen zo niet hergebruiken.

Voor het huidige project is dat geen probleem, maar het is wel een bewuste beperking.

5. Hoe je dit kort kan samenvatten in je mondeling

Je zou ongeveer zoiets kunnen zeggen (in je eigen woorden natuurlijk):

“We hebben gekozen voor één centrale template inventory.html die het volledige Figma-inventoryscherm bevat: sidebar, item-cards, search & filter en het reservations-paneel. Die vier onderdelen horen functioneel en visueel echt samen, en worden allemaal gevoed door dezelfde route inventory(). Daarom hebben we ze niet verder opgesplitst in aparte bestanden.”

“Alle andere acties – toevoegen, reserveren en bewerken – hebben hun eigen, smalle templates die base.html extenden. Dat houdt de views voor die use-cases eenvoudig: elke pagina doet precies één ding. De echte logica zit in routes.py, waar we nu een duidelijke scheiding hebben tussen add_item, use_item, edit_item, edit_material, update_quantity en delete_reservation.”

“In een grotere productie-applicatie zouden we sommige delen (zoals de item-card of de sidebar) misschien als aparte component-templates of macros uitwerken, maar voor deze scope zou dat vooral complexiteit toevoegen. Belangrijker was dat de UI 1-op-1 overeenkomt met de Figma-mock-up, en dat hebben we bereikt.”

Als je wil, kan ik nog een superkorte “architectuur slide” voor je schrijven (bulletpoints) die je letterlijk in een presentatie kan plakken.


   # Temporary: simulate logged in user (remove once real login exists)
    if "username" not in session:
        session["username"] = "Frédéric De Haes" #PAS OP MOET AFH ZIJN VAN LOGIN
    if "company_name" not in session:
        session["company_name"] = "Primetals"