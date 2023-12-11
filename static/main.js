import { $ } from "/static/jquery/src/jquery.js";

// Make Table Sortable
export function make_table_sortable(tableElem)
{
    tableElem.find("thead tr td.number-col").on("click", {table: tableElem}, sort_score_graded_or_weight);
    tableElem.find("thead tr td.due-date").on("click", {table: tableElem}, sort_due_date);
}

function sort_due_date(eventObj)
{
    let $column = $(eventObj.currentTarget);
    let table = $(eventObj.data.table);
    // Unsorted -> ascending
    if (!$column.hasClass("sort-asc") && !$column.hasClass("sort-desc"))
    {
        // Sort ascending order
        $column.addClass("sort-asc");

        // Get table body, then get children and convert to array
        let body = $((table.find("tbody")[0]).children).toArray();

        body.sort((a, b) =>
        {
            let aNum = parseFloat($(a).find("td.date-data").data("value"));
            let bNum = parseFloat($(b).find("td.date-data").data("value"));
            if (isNaN(aNum) || isNaN(bNum))
            {
                return NaN;
            }
            return aNum - bNum;
        });

        $(body).appendTo("tbody");
    }
    // Ascending -> descending
    else if ($column.hasClass("sort-asc"))
    {
        // Sort descending order
        $column.removeClass("sort-asc").addClass("sort-desc");

        // Get table body, then get children and convert to array
        let body = $((table.find("tbody")[0]).children).toArray();

        body.sort((a, b) =>
        {
            let aNum = parseFloat($(a).find("td.date-data").data("value"));
            let bNum = parseFloat($(b).find("td.date-data").data("value"));
            if (isNaN(aNum) || isNaN(bNum))
            {
                return NaN;
            }
            return bNum - aNum;
        });

        $(body).appendTo("tbody");
    }
    // Descending -> unsorted
    else
    {
        // Remove sort
        $column.removeClass("sort-desc");

        // Get table body, then get children and convert to array
        let body = $((table.find("tbody")[0]).children).toArray();

        body.sort((a, b) =>
        {
            let aNum = parseFloat($(a).data("index"));
            let bNum = parseFloat($(b).data("index"));
            if (isNaN(aNum) || isNaN(bNum))
            {
                return NaN;
            }
            return aNum - bNum;
        });

        $(body).appendTo("tbody");
    }
}

function sort_score_graded_or_weight(eventObj)
{
    let $column = $(eventObj.currentTarget);
    let table = $(eventObj.data.table);
    // Unsorted -> ascending
    if (!$column.hasClass("sort-asc") && !$column.hasClass("sort-desc"))
    {
        // Sort ascending order
        $column.addClass("sort-asc");

        // Get table body, then get children and convert to array
        let body = $((table.find("tbody")[0]).children).toArray();

        body.sort((a, b) => {
            let aNum = parseFloat(($(a.lastElementChild)[0]).innerText);
            let bNum = parseFloat(($(b.lastElementChild)[0]).innerText);
            if (isNaN(aNum) || isNaN(bNum))
            {
                return NaN;
            }

            if (aNum < bNum)
            {
                return -1;
            }
            else if (aNum > bNum)
            {
                return 1;
            }
            return 0;
        });

        $(body).appendTo("tbody");
    }
    // Ascending -> descending
    else if ($column.hasClass("sort-asc"))
    {
        // Sort descending order
        $column.removeClass("sort-asc").addClass("sort-desc");

        // Get table body, then get children and convert to array
        let body = $((table.find("tbody")[0]).children).toArray();

        body.sort((a, b) =>
        {
            let aNum = parseFloat(($(a.lastElementChild)[0]).innerText);
            let bNum = parseFloat(($(b.lastElementChild)[0]).innerText);
            if (isNaN(aNum) || isNaN(bNum))
            {
                return NaN;
            }

            if (aNum > bNum)
            {
                return -1;
            }
            else if (aNum < bNum)
            {
                return 1;
            }
            return 0;
        });

        $(body).appendTo("tbody");
    }
    // Descending -> unsorted
    else
    {
        // Remove sort
        $column.removeClass("sort-desc");

        // Get table body, then get children and convert to array
        let body = $((table.find("tbody")[0]).children).toArray();

        body.sort((a, b) =>
        {
            let aNum = parseFloat($(a).data("index"));
            let bNum = parseFloat($(b).data("index"));
            if (isNaN(aNum) || isNaN(bNum))
            {
                return NaN;
            }
            return aNum - bNum;
        });

        $(body).appendTo("tbody");
    }
}

make_table_sortable($("table"));



// Make Form Async
export function make_form_async(formElem)
{
    formElem.on("submit", submit_async);
}

function submit_async(eventObj)
{
    eventObj.preventDefault();
    
    let form = eventObj.currentTarget;
    let formChildren = form.children;

    for (var i = 0; i < formChildren.length; i++)
    {
        $(formChildren[i]).prop("disabled", true);
    }

    const formData = new FormData(form);
    $.ajax(
    {
        url: $(form)[0].action,
        data: formData,
        type: "POST",
        processData: false,
        contentType: false,
        mimeType: $(form)[0].enctype,
        error: (jqXHR, descr) => {console.log("Error submitting form.", descr);},
        success: (data, textStatus, jqXHR) => {$(form).replaceWith("<h3>Upload succeeded.")},
        headers: {'X-CSRFToken': ($(form)[0])[0].value},
        mode: 'same-origin'
    });
}

make_form_async($("form"));



// Make Grade Hypothesized
export function make_grade_hypothesized(tableElem)
{
    //tableElem.find("thead tr td.number-col").on("click", {table: tableElem}, sort_score_graded_or_weight);

    $(tableElem).before('<button id="hypothesize-button" title="Hypothesize your final grade">Hypothesize</button>');
    $("#hypothesize-button").on("click", {table: tableElem}, toggle_grade_guesser);
}

function toggle_grade_guesser(eventObj)
{
    let $button = $(eventObj.currentTarget);
    let $table = $(eventObj.data.table);

    // Get table body, then get children
    let $body = $(($table.find("tbody")[0]).children);
    
    // Hypothesized -> Actual
    if ($table.hasClass("hypothesized"))
    {
        $table.removeClass("hypothesized");
        $button.html("Hypothesize");

        for (var i = 0; i < $body.length; i++)
        {
            let td = $body[i].lastElementChild;
            let html = td.innerHTML;

            if ($(td).hasClass("hypothetical"))
            {
                $(td).removeClass("hypothetical");
                $(td).html($(html).data("actual"));
            }
        }

        calculate_grade($body);
    }
    // Actual -> Hypothesized
    else
    {
        $table.addClass("hypothesized");
        $button.html("Actual Grades");

        for (var i = 0; i < $body.length; i++)
        {
            let td = $body[i].lastElementChild;
            let text = td.innerText;
            if (text === "Ungraded" || text === "Not Due" || text === "Missing")
            {
                $(td).addClass("hypothetical");
                $($(td).html('<input data-actual="'.concat(text, '" type="number" name="', i, '">')))
                .on("change", calculate_grade);
            }
        }
    }
}

make_grade_hypothesized($("table"));

function calculate_grade(eventObj)
{
    let $body = $("tbody tr td.number-col");

    let earned_points = 0;
    let total_points = 0;

    // for each td (percentage)
    for (var i = 0; i < $body.length; i++)
    {
        let td = $body[i];
        let score = NaN;

        // Get value from input field
        if ($(td).hasClass("hypothetical"))
        {
            score = parseFloat($(td).find("input").val());
            // If no score found, skip
            if (isNaN(score))
            {
                continue;
            }
        }
        // Get the already computed score
        else
        {
            score = parseFloat(td.innerText);
            // If no score found, skip
            if (isNaN(score))
            {
                continue;
            }
        }

        let assn_weight = parseFloat($(td).data("weight"));
        total_points = total_points + assn_weight;
        let student_score_for_this_assn = (score / 100) * assn_weight;
        earned_points = earned_points + student_score_for_this_assn;
    }

    let final_grade = (earned_points / total_points) * 100;
    $("#final-grade").html("".concat(final_grade.toFixed(1), "%"));
}