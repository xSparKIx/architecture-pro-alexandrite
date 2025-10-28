import requests
import time
from flask import Flask, jsonify
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Настройка OpenTelemetry
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter())
)

app = Flask(__name__)

# Инструментирование Flask и requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

@app.route('/')
def process_order():
    with tracer.start_as_current_span("service-a-process") as span:
        span.set_attribute("service.name", "service-a")
        span.set_attribute("operation.type", "order_processing")
        
        # Имитация обработки в service-a
        time.sleep(0.1)
        
        # Вызов service-b
        try:
            with tracer.start_as_current_span("call-service-b") as child_span:
                child_span.set_attribute("http.method", "GET")
                child_span.set_attribute("http.url", "http://service-b:8080/")
                
                response = requests.get("http://service-b:8080/", timeout=5)
                child_span.set_attribute("http.status_code", response.status_code)
                
                result = response.json()
                
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            return jsonify({"error": f"Failed to call service-b: {str(e)}"}), 500
        
        return jsonify({
            "service": "service-a",
            "status": "completed",
            "service_b_response": result,
            "trace_id": format(span.get_span_context().trace_id, '032x')
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)