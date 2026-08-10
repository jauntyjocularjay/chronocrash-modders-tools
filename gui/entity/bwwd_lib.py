from PIL import Image

def get_transparency_color(image_path):
    image = Image.open(image_path)
    transparency_color = image.getpixel((image.width - 1, image.height - 1))
    return transparency_color
def find_non_transparent_bbox(image_path, transparency_color):
    image = Image.open(image_path)
    image_data = image.load()
    width, height = image.size
    left, top, right, bottom = width, height, 0, 0
    for y in range(height):
        for x in range(width):
            if image_data[x, y] != transparency_color:
                left = min(left, x)
                top = min(top, y)
                right = max(right, x)
                bottom = max(bottom, y)
    if left == width and top == height and right == 0 and bottom == 0:
        return None
    return left, top, right, bottom

def convert_bbox_to_bbox_format(bbox):
    left, top, right, bottom = bbox
    width = right - left + 1
    height = bottom - top + 1
    return left, top, width, height

def extractBBox(image_path):
	transparency_color = get_transparency_color(image_path)
	bbox = find_non_transparent_bbox(image_path, transparency_color)
	bbox_format = convert_bbox_to_bbox_format(bbox)
	
	return bbox_format



