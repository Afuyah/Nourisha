from flask import url_for

def get_image_url(product):
    if product.images and len(product.images) > 0:
        return url_for('static', filename='uploads/' + product.images[0].cover_image)
    else:
        return url_for('static', filename='uploads/alt_img.png')
