import os

from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileAllowed, FileField, FileRequired
from werkzeug.utils import secure_filename
from wtforms import (
    DecimalField,
    SelectField,
    SubmitField,
    RadioField,
)
from wtforms.validators import DataRequired, NumberRange
from image_processing import (
    open_image,
    color_distance,
    image_color_distribution,
    mark_plot,
)


app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(32)
app.config["RECAPTCHA_USE_SSL"] = False
app.config["RECAPTCHA_PUBLIC_KEY"] = os.environ.get("RECAPTCHA_PUBLIC_KEY")
app.config["RECAPTCHA_PRIVATE_KEY"] = os.environ.get("RECAPTCHA_PRIVATE_KEY")
app.config["SESSION_COOKIE_DOMAIN"] = False
app.config["RECAPTCHA_OPTIONS"] = {"theme": "dark light"}
bootstrap = Bootstrap(app)


class FilterForm(FlaskForm):
    mark_position = SelectField(
        "Положение креста",
        choices=[
            ("horisontal", "Горизонтальное расположение"),
            ("vertical", "Вертикальное расположение"),
        ],
    )
    upload = FileField(
        "Загрузка изображения",
        validators=[
            FileRequired(),
            FileAllowed(
                ["jpg", "png", "jpeg"], "Только изображения необходимо загружать!"
            ),
        ],
        description="jpg, png, jpeg",
    )
    # recaptcha = RecaptchaField()
    red_color = DecimalField(
        label="Процент красного цвета",
        validators=[
            NumberRange(
                min=0, max=100, message="Значение должно быть в диапазоне от 0 до 100"
            ),
        ],
    )
    green_color = DecimalField(
        label="Процент зеленого цвета",
        validators=[
            NumberRange(
                min=0, max=100, message="Значение должно быть в диапазоне от 0 до 100"
            ),
        ],
    )
    blue_color = DecimalField(
        label="Процент синего цвета",
        validators=[
            NumberRange(
                min=0, max=100, message="Значение должно быть в диапазоне от 0 до 100"
            ),
        ],
    )
    radio_color = RadioField(
        "Отображение цвета исходного изображения",
        choices=[
            ("1", "Включить отображение распределения цветов"),
            ("0", "Выключить оторажение распределения цветов"),
        ],
    )
    radio_new_color = RadioField(
        "Отображение цвета обработанного изображения",
        choices=[
            ("1", "Включить отображение распределения цветов нового изображения"),
            ("0", "Выключить отображение распределения цветов нового изображения"),
        ],
    )
    submit = SubmitField("Обработать", render_kw={"class": "myclass"})


@app.route("/", methods=["GET", "POST"])
def default_router():
    form = FilterForm()
    filename = None
    save_file = None
    save_delta_image = None
    save_color_image = None
    save_color_new_image = None
    try:
        if form.validate_on_submit():
            print(f"{request.form.get('checkbox_noise')}")

            filename = os.path.join(
                "./static", secure_filename(form.upload.data.filename)
            )
            form.upload.data.save(filename)
            fimage = open_image(filename)
            red_color = form.red_color.data / 100
            green_color = form.green_color.data / 100
            blue_color = form.blue_color.data / 100
            decode = mark_plot(
                fimage,
                r=red_color,
                g=green_color,
                b=blue_color,
                horisontal=(False if form.mark_position.data == "horisontal" else True),
            )
            if decode is not None:
                split_filename = filename.split(os.sep)
                save_file = (
                    os.sep.join(split_filename[:-1])
                    + os.sep
                    + "mark"
                    + split_filename[-1]
                )

                if form.radio_color.data == "1":
                    save_color_image = (
                        os.sep.join(split_filename[:-1])
                        + os.sep
                        + form.mark_position.data
                        + "_colors_"
                        + ".png"
                    )
                if form.radio_new_color.data == "1":
                    save_color_new_image = (
                        os.sep.join(split_filename[:-1])
                        + os.sep
                        + form.mark_position.data
                        + "_colors_new_"
                        + ".png"
                    )
            else:
                save_file = None
            if save_file is not None:
                decode.save(save_file)
            if save_delta_image is not None:
                delta = color_distance(filename, save_file)
                delta.save(save_delta_image)
            if save_color_image is not None:
                colored = image_color_distribution(filename)
                colored.savefig(
                    save_color_image, bbox_inches="tight", pad_inches=0, dpi=1000
                )
            if save_color_new_image is not None:
                colored = image_color_distribution(save_file)
                colored.savefig(
                    save_color_new_image, bbox_inches="tight", pad_inches=0, dpi=1000
                )

    except Exception as error:
        print(error)
    return render_template(
        "index.html",
        form=form,
        image_name=filename,
        image_name_proc=save_file,
        save_color_new_image=save_color_new_image,
        save_color_image=save_color_image,
    )


@app.route("/info")
def info():
    return render_template(
        "info.html",
        title="about",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port="Heroku")
