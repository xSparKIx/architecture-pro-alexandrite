import time
import random
from flask import Flask, jsonify
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Настройка OpenTelemetry
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter())
)

app = Flask(__name__)

# Инструментирование Flask
FlaskInstrumentor().instrument_app(app)

tracer = trace.get_tracer(__name__)

@app.route('/')
def calculate_price():
    with tracer.start_as_current_span("service-b-calculate") as span:
        span.set_attribute("service.name", "service-b")
        span.set_attribute("operation.type", "price_calculation")
        
        # Имитация сложных расчетов
        time.sleep(0.2)
        
        # Генерация случайной цены
        price = round(random.uniform(100, 1000), 2)
        
        span.set_attribute("calculation.price", price)
        span.set_attribute("calculation.currency", "USD")
        
        # Иногда имитируем ошибку для демонстрации
        if random.random() < 0.1:  # 10% chance of error
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Calculation failed"))
            return jsonify({"error": "Calculation service temporarily unavailable"}), 500
        
        return jsonify({
            "service": "service-b",
            "calculated_price": price,
            "currency": "USD",
            "trace_id": format(span.get_span_context().trace_id, '032x')
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)