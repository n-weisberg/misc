function numberOfItems(arr, item) {
    again = false;
    count = 0;
    arrays = [];
    arr.forEach(element => {
        if (!typeof element == String) {
            arrays.push(element);
            again = true;
        } else {
            if (element == item) {
                count = count + 1;
            }
        }
    });
    if (!again) {
        return count;
    } else {
        sum = 0;
        arrays.forEach(array => {
            sum = sum + numberOfItems(array, item);
        });
        return count + sum;
    }
}

var arr = [
  "apple",
  ["banana", "strawberry", "apple"]
];
console.log(numberOfItems(arr, "apple"));