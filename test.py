from pyrogram import Client, filters

app = Client('polcovnic', phone_number='+380957441355')
with app:
    code = input('Enter code: ')
    app.phone_code = code
    user = app.get_users('self')
    original_text = 'message'
    message = app.send_message(user.id, original_text)
    message.delete()
