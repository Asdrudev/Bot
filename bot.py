import sqlite3
from PIL import Image
import extcolors
import requests
import os
import discord
import json
from dotenv import load_dotenv
load_dotenv()
con = sqlite3.connect("bot.db")
cur = con.cursor()

intents = discord.Intents.default()
intents.message_content = True

# Functions


def get_country_embed(pais):
    response_raw = requests.get(f"https://restcountries.com/v3.1/name/{pais}")
    data = response_raw.json()
    capital = data[0]['capital'][0]
    poblacion = data[0]['population']
    region = data[0]['region']
    bandera = data[0]['flags']['png']
    image = Image.open(requests.get(bandera, stream=True).raw)

    colors = extcolors.extract_from_image(image)
    color1 = colors[0][0][0][0]
    color2 = colors[0][0][0][1]
    color3 = colors[0][0][0][2]

    embed = discord.Embed(
        title=pais.capitalize(),
        description="Informacion del pais",
        color=discord.Colour.from_rgb(color1, color2, color3)
    )
    embed.add_field(name="Capital", value=capital, inline=True)
    embed.add_field(name="Poblacion",
                    value=f"{'{:,}'.format(poblacion)}", inline=True)
    embed.add_field(name="Region", value=region, inline=True)
    embed.set_thumbnail(url=bandera)

    return embed


def get_Team(team_name, equipos):
    for equipo in equipos:
        if equipo["name_en"] == team_name:
            return equipo

# fin fuctions


client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!calc'):
        operacion = message.content.split(' ')[1]

        def calc():
            try:
                if operacion.__contains__("+"):
                    num1 = float(operacion.split("+")[0])
                    num2 = float(operacion.split("+")[1])
                    return num1 + num2
                elif operacion.__contains__("-"):
                    num1 = float(operacion.split("-")[0])
                    num2 = float(operacion.split("-")[1])
                    return num1 - num2
                elif operacion.__contains__("*"):
                    num1 = float(operacion.split("*")[0])
                    num2 = float(operacion.split("*")[1])
                    return num1 * num2
                elif operacion.__contains__("/"):
                    num1 = float(operacion.split("/")[0])
                    num2 = float(operacion.split("/")[1])
                    return num1 / num2
                else:
                    return "Datos invalidos"
            except ValueError:
                return "Numeros invalidos"

        resultado = calc()

        if isinstance(resultado, str):
            await message.channel.send(resultado)
        else:
            await message.channel.send(f"""
            El resultado es: {calc()}
            """)

    if message.content.startswith('!pais'):
        try:
            response_message = await message.channel.send("Cargando...")
            pais = str(message.content.split(" ")[1])
            embed = get_country_embed(pais)
            await response_message.delete()
            await message.channel.send(embed=embed)
        except IndexError:
            id = str(message.author.id)
            res = cur.execute("""
                SELECT country FROM users
                WHERE discord_id = ?
            """, [id])
            country = res.fetchone()[0]
            print(country)
            embed = get_country_embed(country)
            await response_message.delete()
            await message.channel.send(embed=embed)
        except:
            await response_message.delete()
            await message.channel.send("El pais no existe")

    if message.content.startswith('!registro'):
        try:
            id = message.author.id
            name = message.content.split(" ")[1]
            email = message.content.split(" ")[2]
            password = message.content.split(" ")[3]
            passwordConfirm = message.content.split(" ")[4]
            user = {
                "name": name,
                "email": email,
                "password": password,
                "passwordConfirm": passwordConfirm
            }
            # print(user)
            json_body = json.dumps(user)
            print(json_body)
            headers = {
                "Content-Type": "application/json"
            }
            response = requests.post(
                "http://api.cup2022.ir/api/v1/user", data=json_body, headers=headers)
            error = response.json()
            print(error)
            if str(error["message"]).__contains__("duplicate"):
                return await message.channel.send(f"<@{id}> ya estas registrado")
            elif str(error["message"]).__contains__("the minimun allowed length"):
                return await message.channel.send(f"<@{id}> contrasena")
            elif str(error["message"]).__contains__("valid email"):
                return await message.channel.send(f"<@{id}> email ya usado")

            cur.execute("""
               INSERT INTO users (discord_id, name, email, password) VALUES(?, ?, ?, ?)
            """, (id, name, email, password))
            # print("prueba1")
            con.commit()
            # print("prueba2")
            await message.channel.send(f"Registro satisfactorio! <@{id}>")
        except sqlite3.IntegrityError:
            await message.channel.send(f"<@{id}> tu usuario ya se encuentra registrado!")
        
    if message.content.startswith('!eliminar'):
        try:
            id = message.author.id
            res = cur.execute("""
                SELECT * FROM users WHERE discord_id = ?
            """, (id,))
            user = res.fetchone()[0]
            print(user)
            
            cur.execute("""
               DELETE FROM users WHERE discord_id = ?
            """, (id,))
            con.commit()
            await message.channel.send(f"Usuario eliminado <@{id}>")
        except:
            await message.channel.send(f"<@{id}> ya no existe \\!")

    if message.content.startswith('!editar'):
        try:
            id = message.author.id
            pais = message.content.split(" ")[1]
            name = message.content.split(" ")[2]
            # buscar usuario
            res = cur.execute("""
                SELECT * FROM users WHERE discord_id = ?
            """, (id,))
            user = res.fetchone()[0]
            print(user)
            # editar
            cur.execute("""
               UPDATE users
                SET  
                    country = ?,
                    name = ?
                WHERE discord_id = ?    
            """, (pais, name, id))
            con.commit()
        except:
            await message.channel.send(f"<@{id}> fue editado con exito\\!")

    if message.content.startswith("!iniciar"):
        id = message.author.id

        res = cur.execute("""
            SELECT email, password FROM users
            WHERE discord_id = ?
        """, [id])
        data = res.fetchone()

        credenciales = {
            "email": data[0],
            "password": data[1],
        }
        json_body = json.dumps(credenciales)
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post("http://api.cup2022.ir/api/v1/user/login", data=json_body,
        headers=headers).json()
        token = response["data"]["token"]
        cur.execute("""
            UPDATE users
            SET token = ?
            WHERE discord_id = ?    
            """, (token, id))
        con.commit()
        await message.channel.send(f"<@{id}> 😏 Has iniciado sesión 😏 Puedes acceder a las funciones del bot 😎")

    if message.content.startswith("!equipo"):
        id = message.author.id
        pais = str(message.content.split(" ")[1]).capitalize()
        # print(pais)
        res = cur.execute("""
            SELECT token FROM users
            WHERE discord_id = ?
        """, [id])
        token = res.fetchone()[0]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(
            "http://api.cup2022.ir/api/v1/team", headers=headers).json()
        equipos = response["data"]
        informacion_equipo = get_Team(pais, equipos)
        name = informacion_equipo['name_en']  # 1
        grupo = informacion_equipo['groups']  # 2
        # 3 muestra bandera de equipo en discord
        flag = informacion_equipo['flag']
        grup = discord.Embed(
            title=pais.capitalize(),
            description="informacion del equipo",
        )
        grup.add_field(name="Grupo", value=grupo, inline=True)
        grup.set_thumbnail(url=flag)  # 3 muestra bandera de equipos en discord
        await message.channel.send(embed=grup)
       


client.run(os.environ['TOKEN'])
