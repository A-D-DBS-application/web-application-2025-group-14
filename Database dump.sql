-- =====================================
-- PRIMETALS DATA
-- =====================================

INSERT INTO "public"."company" ("company_name")
VALUES ('Primetals');

INSERT INTO "public"."app_user" ("username", "password", "company_name")
VALUES ('Frédéric De Haes', 'wachtwoord', 'Primetals');

INSERT INTO "public"."material" (
    "material_id",
    "material_type",
    "description",
    "lifecycle",
    "brand",
    "price",
    "company_name"
) 
VALUES 
    (
        '1',
        '3SB3400-0M',
        'SCHAKELELEMENT Met 1 schakelelement, 1NC, Montagebewakingscontact, Schroefaansluiting, Voor frontplaatbevestiging !!! Uitlopend product!!! Opvolger is SIRIUS ACT 3SU1 Voorkeurstype opvolger is >>3SU1400-1AA10-1HA0<<',
        'NMV',
        'SIEMENS',
        NULL,
        'Primetals'
    ),
    (
        '2',
        '6ES7138-4CA01-0AA0',
        '*** Spare part *** SIMATIC DP, PM-E power modules for ET 200S; 24 V DC with diagnostics',
        NULL,
        'SIEMENS',
        '26',
        'Primetals'
    ),
    (
        '3',
        '6ES7131-4BD01-0AA0',
        '*** Spare part *** SIMATIC DP, 5 electronic modules for ET 200S, 4DI standard 24 V DC, 15 mm width, 5 units per packing unit',
        NULL,
        'SIEMENS',
        '245',
        'Primetals'
    ),
    (
        '4',
        '3SB3901-0AB',
        'Drager Voor opklikken Van 3 elementen, Voor druk-, Paddestoeldrukknop, Drukknopschakelaars met trekontgrendeling en Drukschakelaar Met frontplaatbevestiging !!! Uitlopend product!!! Opvolger is SIRIUS ACT 3SU1',
        'NMV',
        'SIEMENS',
        NULL,
        'Primetals'
    ),
    (
        '5',
        '3RH1921-1HA22',
        'Auxiliary switch block, 22, 2 NO + 2 NC, EN 50012, 4-pole, screw terminal, for motor contactors, Size S0 .. S3 ! Phased-out product! Successor is SIRIUS 3RH3',
        'NMV',
        'SIEMENS',
        NULL,
        'Primetals'
    ),
    (
        '6',
        '6ES7193-4CB20-0AA0',
        '*** Spare part *** SIMATIC DP, 5 terminal modules TM-E15S24-01 for ET 200S for electronic modules 15 mm width, Screw terminals, 2x4 terminal connections without terminal access to AUX1, AUX1 continuous 5 units per packing unit',
        NULL,
        'SIEMENS',
        '75',
        'Primetals'
    ),
    (
        '7',
        '3RT1015-1AP01',
        'Vermogensrelais, AC-3 7 A, 3 kW / 400 V 1 NO, AC 230 V, 50 / 60 Hz 3-polig, Uitvoering S00 Schroefaansluiting !!! Uitlopend product!!! Opvolger is SIRIUS 3RT2 Voorkeurstype opvolger is >>3RT2015-1AP01<<',
        'NMV',
        'SIEMENS',
        NULL,
        'Primetals'
    ),
    (
        '8',
        '6ES7138-4FB03-0AB0',
        '***Spare part*** SIMATIC DP, Electronics module f. ET200S, 4 F-DO PROFIsafe, 24 V DC/2 A, 30 mm overall width, up to Category 4 (EN 954-1)/ SIL3 (IEC61508)/PLE (ISO13849), can also be used in PROFINET configuration with IM 151-3 HF',
        'alleen omruil- of reparatieservice beschikbaar, opvolger: 6ES7138-4FB04-0AB0',
        'SIEMENS',
        NULL,
        'Primetals'
    ),
    (
        '9',
        '6ES7132-4BD02-0AA0',
        '*** Spare part *** SIMATIC DP, 5 electronic modules for ET 200S, 4 DO standard 24 V DC/0.5 A, 15 mm width, 5 units per packing unit',
        NULL,
        'SIEMENS',
        '332',
        'Primetals'
    ),
    (
        '10',
        '6ES7193-4CA40-0AA0',
        '*** Spare part *** SIMATIC DP, 5 universal terminal modules TM-E15S26-A1 for ET 200S for electronic modules 15 mm width, Screw terminals, 2x6 terminal connections with terminal access to AUX1, AUX1 continuous 5 units per packing unit',
        NULL,
        'SIEMENS',
        '98',
        'Primetals'
    ),
    (
        '11',
        '6ES7193-4CB30-0AA0',
        '*** Spare part *** SIMATIC DP, 5 terminal modules TM-E15C24-01 for ET 200S for electronic modules 15 mm width, spring-type terminals 2x4 terminal connections without terminal access to AUX1, AUX1 continuous 5 units per packing unit',
        NULL,
        'SIEMENS',
        '74',
        'Primetals'
    ),
    (
        '12',
        '6ES7132-4BD32-0AA0',
        '*** Spare part *** SIMATIC DP, 5 electronic modules for ET 200S, 4 DO standard 24 V DC/2 A, 15 mm width, 5 units per packing unit',
        NULL,
        'SIEMENS',
        '643',
        'Primetals'
    ),
    (
        '13',
        '6ES7193-4CA20-0AA0',
        '*** Spare part *** SIMATIC DP, 5 terminal modules TM-E15S24-A1 for ET 200S for electronic modules 15 mm width, Screw terminals, 2x4 terminal connections with terminal access to AUX1, AUX1 continuous 5 units per packing unit',
        NULL,
        'SIEMENS',
        '75',
        'Primetals'
    ),
    (
        '14',
        '3RT1916-1CD00',
        'RC-element AC 127 - 240 V, DC 150 - 250 V Overspanningsbegrenzer voor opbouw op contactors Uitvoering S00 !!! Uitlopend product!!! Opvolger is SIRIUS 3RT2 Voorkeurstype opvolger is >>3RT2916-1CD00<<',
        'NMV',
        'SIEMENS',
        NULL,
        'Primetals'
    ),
    (
        '15',
        '6ES7131-4BD00-0AA0',
        'SIMATIC DP, 5 ELECTRON. MODULES FOR ET 200S, 4 DI STANDARD 24V DC, 15 MM WIDTH, 5 PIECES PER PACKAGING UNIT',
        'niet meer verkrijgbaar, opvolger: 6ES7131-4BD01-0AA0',
        'SIEMENS',
        NULL,
        'Primetals'
    ),
    (
        '16',
        '3SB3610-2EA11',
        'Knevelschakelaar, 22 mm, Rond, Metaal, Zwart, Knevel, kort, 3 schakelstanden I-O-II, TERUGVEREND, Schakelhoek 2x50 graden, Met houder, 1 NO, 1 NO, Schroefaansluiting !!! Uitlopend product!!! Opvolger is SIRIUS ACT 3SU1 Voorkeurstype opvolger is >>3SU1150-2BM60-1NA0<<',
        'NMV',
        'SIEMENS',
        NULL,
        'Primetals'
    ),
    (
        '17',
        '6ES7193-4CF50-0AA0',
        '*** Spare part *** SIMATIC DP, Terminal module TM-E30C46-A1 for ET 200S for electronic modules 30 mm overall width, spring-type terminals 4x 6 terminal connections with terminal access to AUX1, AUX1 continuous',
        NULL,
        'SIEMENS',
        '64',
        'Primetals'
    ),
    (
        '18',
        '6ES7132-4HB01-0AB0',
        '*** Spare part *** SIMATIC DP, 5 electronic modules for ET 200S, 2 DO relay 24 V DC-230 V AC/5 A, 15 mm width, Substitute value output with LED SF (group fault) 5 units per packing unit',
        NULL,
        'SIEMENS',
        '332',
        'Primetals'
    ),
    (
        '19',
        '6ES7390-0AA00-0AA0',
        'SIMATIC S7, Bus connector (replacement part)',
        NULL,
        'SIEMENS',
        '11',
        'Primetals'
    ),
    (
        '20',
        '3SB3420-0B',
        'SCHAKELELEMENT Met 1 schakelelement, 1 NO, Schroefaansluiting, Voor bodembevestiging !!! Uitlopend product!!! Opvolger is SIRIUS ACT 3SU1 Voorkeurstype opvolger is >>3SU1400-2AA10-1BA0<<',
        'NMV',
        'SIEMENS',
        NULL,
        'Primetals'
    ),
    (
        '21',
        '6ES7193-4CA50-0AA0',
        '*** Spare part *** SIMATIC DP, 5 universal terminal modules TM-E15C26-A1 for ET 200S for electronic modules 15 mm width, Spring-type terminals, 2x6 terminal connections with terminal access to AUX1, AUX1 continuous 5 units per packing unit',
        NULL,
        'SIEMENS',
        '98',
        'Primetals'
    ),
    (
        '22',
        '750-613 System Power Supply',
        'System Power Supply; 24 VDC',
        NULL,
        'WAGO',
        '168.7',
        'Primetals'
    ),
    (
        '23',
        '6ES7132-4BB31-0AB0',
        '*** Spare part *** SIMATIC DP, 5 electronic modules for ET 200S, 2 DO High Feature 24 V DC/2 A, 15 mm width, Diagnostics short circuit and wire break, Substitute value output with LED SF (group fault) 5 units per packing unit',
        NULL,
        'SIEMENS',
        '455',
        'Primetals'
    ),
    (
        '24',
        '3SB3901-0AC',
        'Drager met drukstuk Voor bediening van de middelste Van 3 schakelelementen Voor knevel, Veiligheidsslot en Dubbele drukknoppen Met frontplaatbevestiging !!! Uitlopend product!!! Opvolger is SIRIUS ACT 3SU1',
        'NMV',
        'SIEMENS',
        NULL,
        'Primetals'
    );

INSERT INTO "public"."zone" ("zone_id", "zone_name", "company_name")
VALUES
    ('1', '22A', 'Primetals'),
    ('2', '25B', 'Primetals'),
    ('3', '26B', 'Primetals');

INSERT INTO "public"."item" (
    "item_id",
    "material_id",
    "zone_id",
    "purpose",
    "packaging",
    "quantity",
    "comment"
)
VALUES
    ('1',  '5',  '3', 'sell', 'closed', '24', NULL),
    ('2',  '7',  '3', 'sell', 'closed', '22', 'OPVOLGER 3RT2015-1AP01'),
    ('3',  '14', '3', 'sell', 'closed', '27', 'OPVOLGER 3RT2916-1CD00'),
    ('4',  '1',  '3', 'sell', 'closed', '10', '10st/doos . OPVOLGER 3SU1400-1AA10-1HA0'),
    ('5',  '20', '3', 'sell', 'closed', '18', '1 doos: 10 stuks en 1 doos: 8 stuks'),
    ('6',  '16', '3', 'sell', 'closed', '11', NULL),
    ('7',  '4',  '3', 'sell', 'closed', '40', '20st/doos'),
    ('8',  '24', '3', 'sell', 'closed', '10', '10st/doos'),
    ('9',  '15', '2', 'sell', 'closed', '10', '5 ST/DOOS'),
    ('10', '3',  '2', 'sell', 'none',   '14', NULL),
    ('11', '23', '2', 'sell', 'closed', '13', NULL),
    ('12', '9',  '2', 'sell', 'closed', '40', '5 ST/DOOS'),
    ('13', '12', '2', 'sell', 'closed', '40', NULL),
    ('14', '18', '2', 'sell', 'open',   '20', NULL),
    ('15', '2',  '2', 'sell', 'closed', '21', NULL),
    ('16', '8',  '2', 'sell', 'closed', '13', NULL),
    ('17', '13', '2', 'sell', 'closed', '10', NULL),
    ('18', '10', '2', 'sell', 'closed', '90', NULL),
    ('19', '21', '2', 'sell', 'closed', '80', NULL),
    ('20', '6',  '2', 'sell', 'closed', '10', NULL),
    ('21', '11', '2', 'sell', 'closed', '52', NULL),
    ('22', '17', '2', 'sell', 'closed', '22', NULL),
    ('23', '19', '2', 'sell', 'none',   '78', NULL),
    ('24', '22', '1', 'sell', 'open',   '10', '10 stuks in doos ');

INSERT INTO "public"."reservation" (
    "item_id",
    "username",
    "date",
    "quantity",
    "project"
)
VALUES
    (3,  'Frédéric De Haes', '2025-01-10 09:15:00', 5,  'Project ALPHA'),
    (7,  'Frédéric De Haes', '2025-01-12 14:22:00', 2,  'Testlijn uitbreiding'),
    (14, 'Frédéric De Haes', '2025-01-15 08:05:00', 4,  'Onderhoud cel 2'),
    (19, 'Frédéric De Haes', '2025-01-16 11:47:00', 10, 'Upgrade PLC-kast'),
    (1,  'Frédéric De Haes', '2025-01-18 16:33:00', 3,  'Proefopstelling X'),
    (22, 'Frédéric De Haes', '2025-01-19 10:00:00', 6,  'Demo voor klant'),
    (9,  'Frédéric De Haes', '2025-01-20 13:12:00', 1,  'Kleine herstelling'),
    (24, 'Frédéric De Haes', '2025-01-21 09:00:00', 2,  'Eindcontrole lijn 4');


-- =====================================
-- UGENT DATA
-- =====================================

INSERT INTO "public"."company" ("company_name")
VALUES ('UGent');

INSERT INTO "public"."app_user" ("username", "password", "company_name") 
VALUES
    ('Groep 14',     'wachtwoord', 'UGent'),
    ('Medewerker',   'wachtwoord', 'Primetals'),
    ('Test Student', 'wachtwoord', 'UGent');

INSERT INTO "public"."material" (
    "material_id",
    "material_type",
    "description",
    "brand",
    "price",
    "lifecycle",
    "company_name"
)
VALUES
    (101, 'E-METER',  'Digitale multimeter voor labo',     'VOLTCRAFT',   45,  'GOOD', 'UGent'),
    (102, 'CABLESET', 'Set krokodilklemmen',               'BRENNENSTUHL', 8,  'GOOD', 'UGent'),
    (103, 'TEMP-NTC', 'Temperatuursensor NTC 10k',         'OMRON',        3,  'NEW',  'UGent'),
    (104, 'ARD-MEGA', 'Arduino Mega ontwikkelbord',        'Arduino',     38,  'NEW',  'UGent'),
    (105, 'PWR-30V',  'Labvoeding 0–30V 5A',               'PeakTech',   120,  'USED', 'UGent'),
    (106, 'RES-BOX',  'Assortiment weerstanden 600 stuks', 'Velleman',    12,  'NEW',  'UGent');

INSERT INTO "public"."zone" ("zone_id", "zone_name", "company_name")
VALUES
    (10, 'EL1', 'UGent'),
    (11, 'EL2', 'UGent'),
    (12, 'ROB', 'UGent');

INSERT INTO "public"."item" (
    "item_id",
    "material_id",
    "zone_id",
    "purpose",
    "packaging",
    "quantity",
    "comment"
)
VALUES
    (201, 101, 10, 'keep', 'open',   12, 'Gebruikt in basiselectriciteit'),
    (202, 102, 10, 'keep', 'open',   30, NULL),
    (203, 103, 11, 'keep', 'closed', 50, 'NTC 10k sensoren'),
    (204, 104, 11, 'keep', 'closed', 8,  'Voor projecten microcontrollers'),
    (205, 105, 12, 'keep', 'none',   4,  'Beperkte voorraad'),
    (206, 106, 10, 'keep', 'closed', 15, 'Gebruik in alle practica');

INSERT INTO "public"."reservation" (
    "item_id",
    "username",
    "date",
    "quantity",
    "project"
)
VALUES
    (201, 'Groep 14',     '2025-02-01 09:00:00', 4, 'Practicum Elektriciteit'),
    (204, 'Groep 14',     '2025-02-03 14:30:00', 2, 'Microcontrollerproject'),
    (205, 'Groep 14',     '2025-02-05 10:15:00', 1, 'Robotica Testopstelling'),
    (202, 'Groep 14',     '2025-02-06 11:45:00', 6, 'Spanning/Stroom proef'),
    (203, 'Test Student', '2025-02-07 08:15:00', 5, 'PID Temperatuurregeling Demo');

INSERT INTO "public"."reservation" (
    "item_id",
    "username",
    "date",
    "quantity",
    "project"
) 
VALUES
    (1,  'Medewerker', '2025-02-10 09:00:00', 2, 'Magazijn inventaris'),
    (7,  'Medewerker', '2025-02-11 14:20:00', 1, 'Herstelling schakelkast'),
    (14, 'Medewerker', '2025-02-12 08:45:00', 3, 'Upgrade lijn 3'),
    (22, 'Medewerker', '2025-02-13 16:30:00', 4, 'Klantdemo voorbereiding');

INSERT INTO "public"."reservation" (
    "item_id",
    "username",
    "date",
    "quantity",
    "project"
)
VALUES
    (201, 'Test Student', '2025-02-08 10:30:00', 3, 'Sensoropstelling test'),
    (204, 'Test Student', '2025-02-09 13:10:00', 1, 'Arduino demo'),
    (206, 'Test Student', '2025-02-10 15:55:00', 5, 'Weerstanden oefenreeks'),
    (202, 'Test Student', '2025-02-11 11:05:00', 4, 'Basis labo oefening');
