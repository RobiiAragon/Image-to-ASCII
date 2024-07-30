from PIL import Image
#By Jesus Roberto Aragon Lopez
#https://github.com/RobiiAragon

# Mapa de caracteres ASCII en orden creciente de densidad
ASCII_CHARS = "@%#*+=-:. "

def resize_image(image, new_width=100):
    width, height = image.size
    ratio = height / width / 1.65  # Ajusta la proporción de la imagen
    new_height = int(new_width * ratio)
    resized_image = image.resize((new_width, new_height))
    return resized_image

def grayscale_image(image):
    grayscale_image = image.convert("L")
    return grayscale_image

def pixels_to_ascii(image):
    pixels = image.getdata()
    ascii_str = "".join([ASCII_CHARS[pixel // 32] for pixel in pixels])
    return ascii_str

def convert_image_to_ascii(image_path, new_width=100):
    try:
        image = Image.open(image_path)
    except Exception as e:
        print(e)
        return

    image = resize_image(image, new_width)
    image = grayscale_image(image)
    
    ascii_str = pixels_to_ascii(image)
    img_width = image.width
    ascii_str_len = len(ascii_str)
    ascii_img = "\n".join([ascii_str[i:(i+img_width)] for i in range(0, ascii_str_len, img_width)])
    
    return ascii_img

def main():
    image_path = input("Introduce la ruta de la imagen: ")
    ascii_art = convert_image_to_ascii(image_path)
    if ascii_art:
        with open("ascii_image.txt", "w") as f:
            f.write(ascii_art)
        print(ascii_art)

if __name__ == "__main__":
    main()
