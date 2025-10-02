// 常數定義
const PLACE_TYPE_MIN = 1;
const PLACE_TYPE_MAX = 3;
const TOURIST_FOOD_TYPE_MIN = 5;
const TOURIST_FOOD_TYPE_MAX = 10;
const MAX_TRIP_DAYS = 3;
const MAX_MONTHS_AHEAD = 1;

// 表單初始化
function initializeForm() {
    // 設定能選擇的最小時間
    updateMinDateTime();
    setInterval(updateMinDateTime, 60000);
    // 實時驗證旅行偏好設定
    initializeBasicInfoValidation();
    // 實時驗證旅行日期
    initializeTripDateValidation();
    // 實時驗證旅行時間
    initializeDailyTimeValidation();
    // 實時更新權重數值
    initializeWeightSliders();
    // 實時disable選擇數量已達上限之類型以及顯示已選擇數量
    initializeTypeSelections();
    // 修改表單提交處理
    initializeFormSubmission();
}

// 更新目前時間
function updateMinDateTime() {
    const dateRange = getCurrentDateTime();
    const startTimeInput = document.getElementById('startTime');
    const endTimeInput = document.getElementById('endTime');

    // Set minimum and maximum dates for start time
    startTimeInput.min = dateRange.min;
    startTimeInput.max = dateRange.max;

    // Set minimum and maximum dates for end time
    endTimeInput.min = dateRange.min;
    endTimeInput.max = dateRange.max;

    // If startTimeInput has a value, update endTimeInput's max value
    if (startTimeInput.value) {
        const maxEndDate = new Date(startTimeInput.value);
        maxEndDate.setDate(maxEndDate.getDate() + MAX_TRIP_DAYS);
        // Ensure end date doesn't exceed one month limit
        const oneMonthDate = new Date(dateRange.max);
        endTimeInput.max = maxEndDate > oneMonthDate ? oneMonthDate.toISOString().slice(0, 16) : maxEndDate.toISOString().slice(0, 16);
    }

    // Validate existing values
    const now = new Date();
    const oneMonthFromNow = new Date(dateRange.max);

    if (startTimeInput.value) {
        const startDate = new Date(startTimeInput.value);
        if (startDate < now) {
            setInvalidWithMessage(startTimeInput, 'startTimeFeedback', '不可選擇過去的時間');
        } else if (startDate > oneMonthFromNow) {
            setInvalidWithMessage(startTimeInput, 'startTimeFeedback', '請選擇一個月內的時間');
        }
    }

    if (endTimeInput.value) {
        const endDate = new Date(endTimeInput.value);
        if (endDate < now) {
            setInvalidWithMessage(endTimeInput, 'endTimeFeedback', '不可選擇過去的時間');
        } else if (endDate > oneMonthFromNow) {
            setInvalidWithMessage(endTimeInput, 'endTimeFeedback', '請選擇一個月內的時間');
        }
    }
}

// 取得現在時間
function getCurrentDateTime() {
    const now = new Date();
    return {
        min: now.toISOString().slice(0, 16), // Current date-time
        max: new Date(now.setMonth(now.getMonth() + MAX_MONTHS_AHEAD)).toISOString().slice(0, 16) // One month ahead
    };
}

// 實時驗證旅行偏好設定
function initializeBasicInfoValidation() {
    // 旅行名稱驗證
    const tripNameInput = document.getElementById('tripName');
    tripNameInput.addEventListener('input', () => {
        validateField(tripNameInput, '請輸入旅行名稱', value => value.trim().length > 0);
    });

    // 出遊縣市驗證
    const citySelect = document.getElementById('city');
    citySelect.addEventListener('change', () => {
        validateField(citySelect, '請選擇出遊縣市', value => value !== '');
    });

    // 預算限制驗證
    const budgetSelect = document.getElementById('budget');
    budgetSelect.addEventListener('change', () => {
        validateField(budgetSelect, '請選擇預算限制', value => value !== '');
    });

    // 旅遊模式驗證
    const travelModeInputs = document.querySelectorAll('input[name="travelMode"]');
    travelModeInputs.forEach(input => {
        input.addEventListener('change', () => {
            validateRadioGroup(travelModeInputs, '請選擇旅遊模式');
        });
    });
}

// 實時旅程日期時間驗證，並回傳是否有效
function validateTripDates() {
    const startTimeInput = document.getElementById('startTime');
    const endTimeInput = document.getElementById('endTime');
    const dateRange = getCurrentDateTime();
    const startTime = new Date(startTimeInput.value);
    const endTime = new Date(endTimeInput.value);
    const now = new Date();
    const oneMonthFromNow = new Date(dateRange.max);
    let isValid = true;

    // Validate start time
    if (!startTimeInput.value) {
        setInvalidWithMessage(startTimeInput, 'startTimeFeedback', '請選擇啟程時間');
        isValid = false;
    } else if (startTime < now) {
        setInvalidWithMessage(startTimeInput, 'startTimeFeedback', '不可選擇過去的時間');
        isValid = false;
    } else if (startTime > oneMonthFromNow) {
        setInvalidWithMessage(startTimeInput, 'startTimeFeedback', '請選擇一個月內的時間');
        isValid = false;
    } else {
        clearValidationMessage(startTimeInput, 'startTimeFeedback');
    }

    // Validate end time
    if (!endTimeInput.value) {
        setInvalidWithMessage(endTimeInput, 'endTimeFeedback', '請選擇回程時間');
        isValid = false;
    } else if (endTime < now) {
        setInvalidWithMessage(endTimeInput, 'endTimeFeedback', '不可選擇過去的時間');
        isValid = false;
    } else if (endTime > oneMonthFromNow) {
        setInvalidWithMessage(endTimeInput, 'endTimeFeedback', '請選擇一個月內的時間');
        isValid = false;
    } else if (endTime <= startTime && startTimeInput.value) {
        setInvalidWithMessage(endTimeInput, 'endTimeFeedback', '回程時間必須晚於啟程時間');
        isValid = false;
    } else {
        // Check if within MAX_TRIP_DAYS
        const maxEndDate = new Date(startTime);
        maxEndDate.setDate(maxEndDate.getDate() + MAX_TRIP_DAYS);

        if (endTime > maxEndDate) {
            setInvalidWithMessage(endTimeInput, 'endTimeFeedback', `回程時間不可超過去程時間${MAX_TRIP_DAYS}天後`);
            isValid = false;
        } else {
            clearValidationMessage(endTimeInput, 'endTimeFeedback');
        }
    }

    return isValid;
}


// 實時驗證旅行日期
function initializeTripDateValidation() {
    const startTimeInput = document.getElementById('startTime');
    const endTimeInput = document.getElementById('endTime');

    startTimeInput.addEventListener('change', () => {
        if (startTimeInput.value) {
            // 設定回程時間最小值為去程時間
            endTimeInput.min = startTimeInput.value;

            // 計算去程時間加上一週的日期
            const maxEndDate = new Date(startTimeInput.value);
            maxEndDate.setDate(maxEndDate.getDate() + MAX_TRIP_DAYS);

            // 格式化日期為 YYYY-MM-DDTHH:mm
            const maxEndDateStr = maxEndDate.toISOString().slice(0, 16);
            endTimeInput.max = maxEndDateStr;

            // 如果當前選擇的回程時間超過一週，清空回程時間並顯示錯誤
            if (endTimeInput.value) {
                const endDate = new Date(endTimeInput.value);
                if (endDate > maxEndDate) {
                    endTimeInput.value = ''; // 清空回程時間
                    setInvalidWithMessage(endTimeInput, 'endTimeFeedback', '回程時間不可超過去程時間一週後');
                }
            }

            validateTripDates();
        }
    });

    endTimeInput.addEventListener('change', validateTripDates);
}

// 實時驗證旅行時間
function initializeDailyTimeValidation() {
    const dailyStartTime = document.getElementById('dailyStartTime');
    const dailyEndTime = document.getElementById('dailyEndTime');

    dailyStartTime.addEventListener('change', () => {
        validateDailyTimes();
    });

    dailyEndTime.addEventListener('change', () => {
        validateDailyTimes();
    });
}

// 每日時間驗證，並回傳是否有效
function validateDailyTimes() {
    const dailyStartTime = document.getElementById('dailyStartTime');
    const dailyEndTime = document.getElementById('dailyEndTime');
    // const dailyStartTimeFeedback = document.getElementById('dailyStartTimeFeedback');
    const dailyEndTimeFeedback = document.getElementById('dailyEndTimeFeedback');
    let isValid = true;

    // 如果有填寫，驗證填寫的是否有效
    if (dailyStartTime.value && dailyEndTime.value) {
        const start = new Date(`2000-01-01T${dailyStartTime.value}`);
        const end = new Date(`2000-01-01T${dailyEndTime.value}`);

        if (end <= start) {
            // 清除原先正確提示
            dailyEndTime.classList.remove('is-valid');
            // 給予錯誤提示
            dailyEndTime.classList.add('is-invalid');
            dailyEndTimeFeedback.textContent = '每日回程時間必須晚於每日啟程時間';
            dailyEndTimeFeedback.style.display = 'block';
            // 設定錯誤
            isValid = false;
        } else {
            // 清除兩個時間的錯誤訊息
            clearValidationMessage(dailyEndTime, 'dailyEndTimeFeedback');
            clearValidationMessage(dailyStartTime, 'dailyStartTimeFeedback');
        }
    // 如果未填寫
    } else {
        if (!dailyStartTime.value) {
            // 給予錯誤提示
            setInvalidWithMessage(dailyStartTime, 'dailyStartTimeFeedback', '請選擇每日啟程時間');
            isValid = false;
        } else {
            // 清除兩個時間的錯誤訊息
            clearValidationMessage(dailyStartTime, 'dailyStartTimeFeedback');
        }

        if (!dailyEndTime.value) {
            // 給予錯誤提示
            setInvalidWithMessage(dailyEndTime, 'dailyEndTimeFeedback', '請選擇每日回程時間');
            isValid = false;
        } else {
            // 清除兩個時間的錯誤訊息
            clearValidationMessage(dailyEndTime, 'dailyEndTimeFeedback');
        }
    }
    return isValid;
}

// 權重滑塊初始化
function initializeWeightSliders() {
    ['priceLevelWeight', 'ratingWeight', 'userRatingTotalWeight', 'ngen'].forEach(sliderId => {
        const slider = document.getElementById(sliderId);
        const valueDisplay = document.getElementById(`${sliderId}Value`);

        slider.addEventListener('input', () => {
            valueDisplay.textContent = parseFloat(slider.value).toFixed(1);
        });
    });
}

// 類型選擇處理
function initializeTypeSelections() {
    initializePlaceTypes();
    initializeTouristTypes();
    initializeFoodTypes();
}

function initializePlaceTypes() {
    const container = document.querySelector('.place-types-container');
    const checkboxes = container.querySelectorAll('.place-type-checkbox');
    const countDisplay = document.getElementById('placeTypesCount');

    checkboxes.forEach(checkbox => {
        const keywordInput = checkbox.closest('.checkbox-wrapper')
            .querySelector('.keyword-input');

        checkbox.addEventListener('change', () => {
            // 更新關鍵字輸入框狀態
            keywordInput.disabled = !checkbox.checked;
            if (!checkbox.checked) {
                keywordInput.value = '';
            }

            updateTypeSelection(
                'place-types-container',
                checkboxes,
                countDisplay,
                PLACE_TYPE_MAX,
                PLACE_TYPE_MIN,
                PLACE_TYPE_MAX
            );
        });
    });
}

function initializeTouristTypes() {
    const container = document.querySelector('.tourist-types-container');
    const checkboxes = container.querySelectorAll('.tourist-type-checkbox');
    const countDisplay = document.getElementById('touristTypesCount');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
            countDisplay.textContent = `已選擇 ${checkedCount} 個類型`;

            // 更新選中狀態和禁用邏輯
            if (checkedCount >= TOURIST_FOOD_TYPE_MAX) {
                // 禁用未選中的選項
                checkboxes.forEach(cb => {
                    if (!cb.checked) {
                        cb.disabled = true;
                        const pillLabel = cb.nextElementSibling;
                        if (pillLabel) {
                            pillLabel.classList.add('disabled');
                        }
                    }
                });
            } else {
                // 啟用所有選項
                checkboxes.forEach(cb => {
                    cb.disabled = false;
                    const pillLabel = cb.nextElementSibling;
                    if (pillLabel) {
                        pillLabel.classList.remove('disabled');
                    }
                });
            }
        });
    });
}

function initializeFoodTypes() {
    const container = document.querySelector('.food-types-container');
    const checkboxes = container.querySelectorAll('.food-type-checkbox');
    const countDisplay = document.getElementById('foodTypesCount');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
            countDisplay.textContent = `已選擇 ${checkedCount} 個類型`;

            // 更新選中狀態和禁用邏輯
            if (checkedCount >= TOURIST_FOOD_TYPE_MAX) {
                // 禁用未選中的選項
                checkboxes.forEach(cb => {
                    if (!cb.checked) {
                        cb.disabled = true;
                        const pillLabel = cb.nextElementSibling;
                        if (pillLabel) {
                            pillLabel.classList.add('disabled');
                        }
                    }
                });
            } else {
                // 啟用所有選項
                checkboxes.forEach(cb => {
                    cb.disabled = false;
                    const pillLabel = cb.nextElementSibling;
                    if (pillLabel) {
                        pillLabel.classList.remove('disabled');
                    }
                });
            }
        });
    });
}

function updateTypeSelection(containerId, checkboxes, countDisplay, maxCount, minCount, maxAllowed) {
    const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
    countDisplay.textContent = `已選擇 ${checkedCount} 個類型`;

    // 更新 checkbox 的驗證狀態
    checkboxes.forEach(checkbox => {
        const wrapper = checkbox.closest('.checkbox-wrapper');
        if (checkedCount >= minCount && checkedCount <= maxAllowed) {
            checkbox.classList.remove('is-invalid');
            checkbox.classList.add('is-valid');
        }
    });

    // 處理禁用狀態
    if (checkedCount >= maxCount) {
        checkboxes.forEach(cb => {
            if (!cb.checked) {
                cb.disabled = true;
                const wrapper = cb.closest('.checkbox-wrapper');
                wrapper.classList.add('disabled');
            }
        });
    } else {
        checkboxes.forEach(cb => {
            cb.disabled = false;
            const wrapper = cb.closest('.checkbox-wrapper');
            wrapper.classList.remove('disabled');
        });
    }
}

// 修改表單提交處理
function initializeFormSubmission() {
    const form = document.getElementById('tripPlannerForm');

    form.addEventListener('submit', (event) => {
        event.preventDefault();

        // 清除之前的驗證狀態
        clearValidationStates();

        // 執行所有驗證
        const isBasicInfoValid = validateBasicInfo();
        const isTimeValid = validateAllTimes();
        const isTypeSelectionsValid = validateTypeSelections();

        // 只有當所有驗證都通過時才提交
        if (isBasicInfoValid && isTimeValid && isTypeSelectionsValid) {
            form.submit();
        } else {
            // 滾動到第一個錯誤元素
            const firstError = form.querySelector('.is-invalid') ||
                             form.querySelector('.invalid-feedback[style="display: block;"]');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });
}

// 清除之前的驗證狀態，確保正確重置時間驗證狀態
function clearValidationStates() {
    const form = document.getElementById('tripPlannerForm');
    form.classList.remove('was-validated');

    // 清除所有驗證狀態和訊息
    const elementsWithValidation = document.querySelectorAll('.is-invalid, .is-valid');
    elementsWithValidation.forEach(element => {
        element.classList.remove('is-invalid', 'is-valid');
        // 查找相關的 feedback 元素並清除
        const feedbackElement = element.nextElementSibling;
        if (feedbackElement && feedbackElement.classList.contains('invalid-feedback')) {
            feedbackElement.textContent = '';
            feedbackElement.style.display = 'none';
        }
    });

    // 額外清除特定的 feedback 元素
    ['startTimeFeedback', 'endTimeFeedback',
     'dailyStartTimeFeedback', 'dailyEndTimeFeedback'].forEach(id => {
        const feedback = document.getElementById(id);
        if (feedback) {
            feedback.textContent = '';
            feedback.style.display = 'none';
        }
    });

    ['place-types-container', 'tourist-types-container', 'food-types-container'].forEach(containerId => {
        const container = document.querySelector(`.${containerId}`);
        if (container) {
            const feedback = container.querySelector('.invalid-feedback');
            if (feedback) {
                feedback.style.display = 'none';
            }
            container.classList.remove('has-error');
        }
    });

}

function validateBasicInfo() {
    const tripNameInput = document.getElementById('tripName');
    const citySelect = document.getElementById('city');
    const budgetSelect = document.getElementById('budget');
    const travelModeInputs = document.querySelectorAll('input[name="travelMode"]');

    const isTripNameValid = validateField(tripNameInput, '請輸入旅行名稱', value => value.trim().length > 0);
    const isCityValid = validateField(citySelect, '請選擇出遊縣市', value => value !== '');
    const isBudgetValid = validateField(budgetSelect, '請選擇預算限制', value => value !== '');
    const isTravelModeValid = validateRadioGroup(travelModeInputs, '請選擇旅遊模式');

    return isTripNameValid && isCityValid && isBudgetValid && isTravelModeValid;
}

// 驗證所有時間相關欄位
function validateAllTimes() {
    const startTimeValid = validateField(
        document.getElementById('startTime'),
        '請選擇啟程時間',
        value => {
            if (!value) return false;
            const selectedTime = new Date(value);
            const now = new Date();
            return selectedTime >= now;
        }
    );

    const endTimeValid = validateField(
        document.getElementById('endTime'),
        '請選擇回程時間',
        value => {
            if (!value) return false;
            const selectedTime = new Date(value);
            const startTime = new Date(document.getElementById('startTime').value);
            return selectedTime > startTime;
        }
    );

    const dailyTimesValid = validateDailyTimes();

    return startTimeValid && endTimeValid && dailyTimesValid;
}

// 修改類型選擇驗證
function validateTypeSelections() {
    let isValid = true;

    const placeTypesCount = countSelectedCheckboxes('place-type-checkbox');
    const placeTypesContainer = document.querySelector('.place-types-container');
    const placeFeedback = placeTypesContainer.querySelector('.invalid-feedback');

    if (placeTypesCount < PLACE_TYPE_MIN || placeTypesCount > PLACE_TYPE_MAX) {
        isValid = false;
        placeFeedback.style.display = 'block';
        placeTypesContainer.querySelectorAll('.place-type-checkbox').forEach(cb => {
            cb.classList.add('is-invalid');
            cb.classList.remove('is-valid');
        });
    } else {
        placeFeedback.style.display = 'none';
        placeTypesContainer.querySelectorAll('.place-type-checkbox').forEach(cb => {
            cb.classList.remove('is-invalid');
            cb.classList.add('is-valid');
        });
    }

    // 驗證觀光景點類型
    const touristTypesCount = countSelectedCheckboxes('tourist-type-checkbox');
    if (touristTypesCount < TOURIST_FOOD_TYPE_MIN || touristTypesCount > TOURIST_FOOD_TYPE_MAX) {
        showTypeError('tourist-types-container', '請選擇5-10個觀光景點類型');
        isValid = false;
    } else {
        hideTypeError('tourist-types-container');
    }

    // 驗證食物類型
    const foodTypesCount = countSelectedCheckboxes('food-type-checkbox');
    if (foodTypesCount < TOURIST_FOOD_TYPE_MIN || foodTypesCount > TOURIST_FOOD_TYPE_MAX) {
        showTypeError('food-types-container', '請選擇5-10個食物類型');
        isValid = false;
    } else {
        hideTypeError('food-types-container');
    }

    return isValid;
}

// 修改驗證欄位的函數
function validateField(element, errorMessage, validationFn) {
    const isValid = validationFn(element.value);
    const feedback = element.nextElementSibling;

    element.classList.remove('is-valid', 'is-invalid');

    if (isValid) {
        element.classList.add('is-valid');
        if (feedback) {
            feedback.textContent = '';
            feedback.style.display = 'none';
        }
    } else {
        element.classList.add('is-invalid');
        if (feedback) {
            feedback.textContent = errorMessage;
            feedback.style.display = 'block';
        }
    }
    return isValid;
}

// 驗證單選按鈕組
function validateRadioGroup(radioInputs, errorMessage) {
    const isValid = Array.from(radioInputs).some(input => input.checked);
    const feedback = radioInputs[0].closest('.form-group').querySelector('.invalid-feedback');

    if (isValid) {
        radioInputs.forEach(input => input.classList.remove('is-invalid'));
        radioInputs.forEach(input => input.classList.add('is-valid'));
        if (feedback) feedback.style.display = 'none';
    } else {
        radioInputs.forEach(input => input.classList.add('is-invalid'));
        if (feedback) {
            feedback.textContent = errorMessage;
            feedback.style.display = 'block';
        }
    }
    return isValid;
}

function clearValidationMessage(element, feedbackId) {
    element.classList.remove('is-invalid');
    element.classList.add('is-valid');
    const feedback = document.getElementById(feedbackId);
    if (feedback) {
        feedback.textContent = '';
        feedback.style.display = 'none';
    }
}


function showTypeError(containerId, message) {
    const container = document.querySelector(`.${containerId}`);
    const feedback = container.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.textContent = message;
        feedback.classList.remove('d-none');
        feedback.style.display = 'block';
    }
}

function hideTypeError(containerId) {
    const container = document.querySelector(`.${containerId}`);
    const feedback = container.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.classList.add('d-none');
        feedback.style.display = 'none';
    }
}

function setInvalidWithMessage(element, feedbackId, message) {
    element.classList.remove('is-valid');
    element.classList.add('is-invalid');
    const feedback = document.getElementById(feedbackId);
    if (feedback) {
        feedback.textContent = message;
        feedback.style.display = 'block';
    }
}

function validateRequiredFields() {
    let isValid = true;

    // 檢查所有必填欄位
    document.querySelectorAll('[required]').forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            const feedback = field.nextElementSibling;
            if (feedback && feedback.classList.contains('invalid-feedback')) {
                feedback.classList.remove('d-none');
                feedback.style.display = 'block';
            }
            isValid = false;
        } else {
            field.classList.add('is-valid');
        }
    });

    return isValid;
}

function validateTypeRange(containerId, count, min, max, errorMessage) {
    const container = document.querySelector(`.${containerId}`);
    const feedback = container.querySelector('.invalid-feedback');

    if (count < min || count > max) {
        feedback.textContent = errorMessage;
        feedback.style.display = 'block';
        container.classList.add('has-error');
        return false;
    } else {
        feedback.style.display = 'none';
        container.classList.remove('has-error');
        return true;
    }
}

function countSelectedCheckboxes(className) {
    return document.querySelectorAll(`.${className}:checked`).length;
}

// DOM 載入完成後初始化
document.addEventListener('DOMContentLoaded', initializeForm);

document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有 toast
    var toastElList = [].slice.call(document.querySelectorAll('.toast'));
    var toastList = toastElList.map(function(toastEl) {
        return new bootstrap.Toast(toastEl, {
            autohide: false  // 設置為不自動隱藏
        });
    });
});