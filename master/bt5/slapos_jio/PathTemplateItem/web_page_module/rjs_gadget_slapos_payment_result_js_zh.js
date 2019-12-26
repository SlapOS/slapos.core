/*jslint nomen: true, indent: 2, maxlen: 80 */
/*global window, rJS, RSVP, Handlebars */
(function (window, rJS, RSVP, Handlebars) {
  "use strict";
  var gadget_klass = rJS(window),
    message_source = gadget_klass.__template_element
                         .getElementById("message-template")
                         .innerHTML,
    message_template = Handlebars.compile(message_source);

  /////////////////////////////
  // parameters
  /////////////////////////////

  /////////////////////////////
  // methods
  /////////////////////////////
  gadget_klass

    /////////////////////////////
    // state
    /////////////////////////////

    /////////////////////////////
    // ready
    /////////////////////////////

    /////////////////////////////
    // acquired methods
    /////////////////////////////

    /////////////////////////////
    // published methods
    /////////////////////////////

    /////////////////////////////
    // declared methods
    /////////////////////////////

    // -------------------.--- Render ------------------------------------------
    .declareMethod("render", function (my_option_dict) {
      var gadget = this,
          result = window.location.hash.replace("#payment_", "").split("?")[0],
          payment = window.location.hash.split("payment=")[1];

      return gadget.getElement()
        .push(function (element) {
          var message, advice, page_title, payment_message = "",
              payment_reference = "", payment_message_footer = "";
          if (result === "success") {
            page_title = "感谢您的付款";
            message = "您的订单已成功生成。";
            advice = "待我们从银行收到付款确认书后，您将收到一封电子邮件，其中包含有关所订购服务器的详细说明和信息。";
            payment_message = "您的支付单号是";
            payment_reference = payment.split("/")[1];
            payment_message_footer = "如果您有任何疑问或在接下来的24小时内未收到任何信息，请通过以下方式与我们联系";
          } else if (result === "cancel") {
            page_title = "付款已取消";
            message = "您已取消付款流程。";
            advice = "如果您要继续进行预订，请考虑重新启动该流程。";
          } else if (result === "error") {
            page_title = "付款出错了";
            message = "付款时发生错误。";
            advice = "请稍后再试，或通过以下地址与我们联系。";
          } else if (result === "refused" || result === "referral") {
            page_title = "付款被拒绝";
            message = "很抱歉，该支付已被付款系统拒绝";
            advice = "请与您的银行联系或使用其他信用卡。";
            payment_message_footer = "如有任何疑问，请通过以下方式与我们联系";
          } else if (result === "return") {
            page_title = "付款未完成";
            message = "您尚未完成付款。";
            advice = "如果要继续预订，请考虑重新启动流程。";
            payment_message_footer = "如有任何疑问，请通过以下方式与我们联系";
          } else if (result === "already_registered") {
            page_title = "付款记录已生成";
            message = "您的付款记录已生成。 如果您对此付款有任何疑问，请与我们联系。";
            payment_message_footer = "如果您有任何疑问或在接下来的24小时内未收到任何信息，请通过以下方式与我们联系";
          } else {
            throw new Error("Unknown action to take: " + result);
          }
          element.innerHTML = message_template({
            page_title: page_title,
            message_to_acknowledge: message,
            advice: advice,
            payment_message_header: payment_message,
            payment_reference: payment_reference,
            payment_message_footer: payment_message_footer
          });
          return page_title;
        });
    })

    /////////////////////////////
    // declared jobs
    /////////////////////////////

    /////////////////////////////
    // declared service
    /////////////////////////////
    .declareService(function () {
      var gadget = this;
      return new RSVP.Queue()
        .push(function () {
          return gadget.render({});
        });
    });
    /////////////////////////////
    // on Event
    /////////////////////////////

}(window, rJS, RSVP, Handlebars));