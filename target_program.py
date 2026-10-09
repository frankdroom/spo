def validate_input(val_str):
    if val_str.isdigit():
        num = int(val_str)
        if num > 0:
            return num
        else:
            return -1
    else:
        return 0


def process_status_code(code, mode):
    result_message = ""

    if mode == "detailed":
        match code:
            case 100:
                result_message = "Status 100: Continue processing"
            case 200:
                result_message = "Status 200: Success"
            case 400:
                result_message = "Status 400: Bad Request"
            case 500:
                result_message = "Status 500: Internal Server Error"
            case _:
                result_message = "Status Unknown"
    else:
        result_message = f"Basic Status: {code}"

    return result_message


def calculate_statistics(data_list):
    total_sum = 0
    valid_count = 0

    for item in data_list:
        if item > 0:
            total_sum += item
            valid_count += 1
        elif item == 0:
            print("Предупреждение: обнаружен нуль.")
        else:
            continue

    if valid_count > 0:
        avg_value = total_sum / valid_count
    else:
        avg_value = 0.0

    return total_sum, avg_value


def main():
    print("=== Запуск аналитического модуля ===\n")

    input_attempts = 0
    max_attempts = 3
    user_limit = 0

    while input_attempts < max_attempts:
        raw_val = input("Введите положительное число элементов (1-10): ")
        user_limit = validate_input(raw_val)

        if user_limit > 0:
            print("Ввод успешно принят!")
            break
        elif user_limit == -1:
            print("Ошибка: число должно быть строго больше нуля.")
        else:
            print("Ошибка: введены некорректные символы.")

        input_attempts += 1

    if user_limit <= 0:
        print("Превышено количество попыток ввода. Завершение работы.")
        return

    generated_data = []
    counter = 1

    while counter <= user_limit:
        if counter % 2 == 0:
            generated_data.append(counter * 10)
        else:
            generated_data.append(counter * 5)
        counter += 1

    print("\nСформированный массив данных:", generated_data)

    total, average = calculate_statistics(generated_data)
    print(f"Сумма элементов: {total}, Среднее значение: {average:.2f}")

    status_code = 200 if total > 20 else 400

    status_text = process_status_code(status_code, mode="detailed")
    print("Результат проверки статуса:", status_text)


if __name__ == "__main__":
    main()