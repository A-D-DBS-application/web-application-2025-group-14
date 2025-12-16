[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/DxqGQVx4)


# Short description: 

    (- How to install the app)

        The app is compatible with all devices and is intended to be used in landscape mode, although portrait mode works perfectly fine as well.
        The layout of the item cards may vary depending on the device used; the optimal layout appears on PC, iPad Pro, Surface Pro 7.


    - How to use the app

        The MVP is an inventory management system designed for Primetals. 
        When launching the app, the user is asked to enter their username (e-mail). After logging in, the user arrives at the main screen, where the left side displays a list of Brands for which inventory is available. Clicking on one of these expands the Brand, showing a list of all Material_Type ~ Description’s.

        Clicking on a Material_Type displays the inventory of that Material, the Items, on the right side of the screen. These Items are differentiated by the Zone they are located in, their Packaging, and their Purpose. Each Item also has its own Quantity and Reserved Quantity.
        The first quantity is freely editable, allowing the user to easily add an amount or subtract one if consumed. The Reserved Quantity, however, shows how much of an Item is currently being reserved. This quantity is clickable: selecting it opens a screen with information about the reservations made for that Item.

        To make a Reservation for a certain amount of an Item, the user can click the Reserve button, which opens a new page asking for additional information, the amount and wherefore e.g. Each Item also has an Edit button, which allows for modifications to the Item. Another Edit button appears at the top representing the Material_Type, to modify the Material.

        In the navigation bar above, there are four buttons:

        - Search & Filter
        - Add_Item (to add new stock)
        - Reservations (showing the all reservations)
        - Log Out

        The Reservations-button gives an overview of all reservations, with the option to modify them using the button. When clicking this button, a screen appears where the user can specify whether part of the reserved amount should be returned to stock or not, with possible adjustments.

        Finally, when returning to the main screen (possibly by deselecting a Brand), the user will see a For You page on the right side. This is a custom list of Material_Types that the User has previously viewed or made reservations of; the list can be modified via the Bins. Clicking View Items redirects the user to the corresponding Items, increasing search efficiency above the Search & Filter.


# UI Prototype [onbelangrijk, zie UI (prototype.png)]

    - https://www.figma.com/make/FOkPA0LPCYynYhBK7A0kYn/Group-14---Primetals?node-id=0-1&t=cj4AqcCe58eQ5cuZ-1


# Kanban board

    - https://miro.com/welcomeonboard/dlpQZEU5clJyTzFhN0xycVdzb2ZNbjNEdDZqdncxa2RPbGVBNGRlVUU2UlRjdDRNbEJ4dnFCK0ZodURSN1dtd3RxRkozdm9lSDRUOVJ1V0tpbXdMaFBoL2FsTmJhUERtMXUzMEUyVWV4TWNFVDZ6bUYrMVlUYmEvS1ZDalc4aFRzVXVvMm53MW9OWFg5bkJoVXZxdFhRPT0hdjE=?share_link_id=952220583580


# Feedback sessions

    - Session 1: https://drive.google.com/file/d/1Fa0YxpjtZGw25gkQEN7VB9jRr65ZqKb-/view?usp=sharing

    - Session 2: (link)


# Other links/info

    - Database Design

        https://supabase.com/dashboard/project/dlklychiybmzxpqfadks/database/schemas

    - Complex Algorithm

        'For You'  (will be explained during the presentation) 