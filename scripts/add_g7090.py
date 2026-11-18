import json

filepath = 'app/knowledge.json'

with open(filepath, encoding='utf-8-sig') as f:
    data = json.load(f)

nuevo_tema = {
    "id": "reglamento_adultos_mayores",
    "title": "Reglamento Ley Orgánica Personas Adultas Mayores",
    "keywords": ["g7090", "reglamento", "ley organica", "adultos mayores", "personas mayores", "ley adultos"],
    "response_text": "📋 *Reglamento de la Ley Orgánica para la Atención y Desarrollo Integral de las Personas Adultas Mayores*\n\nConsulta el reglamento completo en:\n👉 https://tuinfo.vercel.app/construccion",
    "image_url": "",
    "is_priority": False
}

# Verificar si ya existe
ids = [t.get('id') for t in data]
if nuevo_tema['id'] in ids:
    print("El tema ya existe, actualizando...")
    for i, t in enumerate(data):
        if t.get('id') == nuevo_tema['id']:
            data[i] = nuevo_tema
            break
else:
    data.append(nuevo_tema)
    print(f"Tema agregado. Total de temas: {len(data)}")

with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("knowledge.json actualizado correctamente.")
print(f"Palabras clave: {nuevo_tema['keywords']}")
