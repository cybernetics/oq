require "option_parser"

require "./oq"

module Oq
  processor = Processor.new

  OptionParser.parse! do |parser|
    parser.banner = "Usage: oq [--help] [oq-arguments] [jq-arguments] jq_filter [file [files...]]"
    parser.on("-h", "--help", "Show this help message.") do
      output = IO::Memory.new

      Process.run("jq", ["-h"], output: output)

      puts parser, output.to_s.lines.tap(&.delete_at(0..1)).join('\n')
      exit
    end
    parser.on("-i FORMAT", "--input FORMAT", "Format of the input data. Supported formats: #{Format.to_s}") { |format| (f = Format.parse?(format)) && !f.xml? ? processor.input_format = f : (puts "Invalid input format: '#{format}'"; exit(1)) }
    parser.on("-o FORMAT", "--output FORMAT", "Format of the output data. Supported formats: #{Format.to_s}") { |format| (f = Format.parse?(format)) ? processor.output_format = f : (puts "Invalid output format: '#{format}'"; exit(1)) }
    parser.on("--indent NUMBER", "Use the given number of spaces for indentation (JSON/XML only).") { |n| processor.indent = n.to_i; processor.args << "--indent"; processor.args << n }
    parser.on("--xml-root ROOT", "Name of the root XML element if converting to XML.") { |r| processor.xml_root = r }
    parser.on("--no-prolog", "Whether the XML prolog should be emitted if converting to XML.") { processor.xml_prolog = false }
    parser.invalid_option do |flag|
      case flag
      when "-n", "--null-input" then processor.null_input = true
      when "--tab"              then processor.tab = true
      end

      processor.args << flag
    end
  end

  processor.process
end
