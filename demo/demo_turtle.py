import turtle

def snowflake(length_side, levels):
    if levels == 0:
        turtle.forward(length_side)
        return
    length_side /= 3.0
    snowflake(length_side, levels-1)
    turtle.left(60)
    snowflake(length_side, levels-1)
    turtle.right(120)
    snowflake(length_side, levels-1)
    turtle.left(60)
    snowflake(length_side, levels-1)

if __name__ == "__main__":
    turtle.speed(0)
    length = 300.0
    turtle.penup()
    turtle.backward(length/2.0)
    turtle.pendown()
    for i in range(3):
        snowflake(length, 4)
        turtle.right(120)
    turtle.hideturtle()

